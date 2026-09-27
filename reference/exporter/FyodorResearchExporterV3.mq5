//+------------------------------------------------------------------+
//|                                FyodorResearchExporterV3.mq5      |
//|  Reproducible MT5 economic-calendar and OHLC research exporter   |
//+------------------------------------------------------------------+
#property copyright   "Fyodor Math Lab"
#property link        "https://github.com/fyodorstudio/lab"
#property version     "3.10"
#property description "Versioned, provenance-preserving MT5 calendar and OHLC exporter."
#property description "Exports immutable raw values, event metadata, release vintages, and a run manifest."
#property script_show_inputs
#property strict

#define EXPORTER_VERSION "3.1.0"
#define SCHEMA_VERSION   "fyodor-mt5-research-export/3.1.0"

input group "=== Export Scope ==="
input bool              ExportCalendar         = true;
input bool              ExportMarketWatchBars  = true;
input string            CalendarCurrencies     = "USD,EUR,GBP,JPY,AUD,CAD,CHF,NZD";
input datetime          CalendarFromDate       = D'2015.01.01 00:00:00';
input datetime          CalendarToDate         = 0;  // 0 = trade-server snapshot time
input datetime          CandleFromDate         = D'2015.01.01 00:00:00';
input datetime          CandleToDate           = 0;  // 0 = trade-server snapshot time
input ENUM_TIMEFRAMES   CandleTimeframe        = PERIOD_H1;

input group "=== Reliability ==="
input int               RequestRetries         = 3;
input int               RetryDelayMilliseconds = 1000;
input bool              ExcludeIncompleteBar   = true;
input bool              ExportOnlyForexSymbols = true;
input bool              StopOnCalendarError    = false;

input group "=== Output ==="
input string            OutputRootPrefix       = "FyodorResearchExport_v3";
input bool              SaveToCommonFolder     = true;
input bool              ShowCompletionDialog   = true;

struct CalendarExportResult
  {
   int events;
   int releases;
   int countries_failed;
   int event_queries_failed;
   int value_queries_failed;
   int event_id_mismatches;
   bool completed;
  };

struct CandleExportResult
  {
   int symbols_seen;
   int symbols_skipped;
   int symbols_exported;
   int symbols_failed;
   long bars_exported;
   bool completed;
  };

datetime g_snapshot_server=0;
datetime g_snapshot_gmt=0;
datetime g_calendar_to=0;
datetime g_candle_to=0;
string   g_export_id="";
string   g_export_root="";
int      g_file_flags=0;

//+------------------------------------------------------------------+
//| Primitive formatting helpers                                    |
//+------------------------------------------------------------------+
string BoolString(const bool value)
  {
   return value ? "true" : "false";
  }

string Int64String(const long value)
  {
   return IntegerToString(value);
  }

string ULongString(const ulong value)
  {
   // Preserve the entire unsigned 64-bit identifier with no narrowing cast.
   return StringFormat("%I64u",value);
  }

string ServerTimeText(const datetime value)
  {
   if(value<=0)
      return "";
   return TimeToString(value,TIME_DATE|TIME_SECONDS);
  }

string CompactTimestamp(const datetime value)
  {
   string result=TimeToString(value,TIME_DATE|TIME_SECONDS);
   StringReplace(result,".","");
   StringReplace(result,":","");
   StringReplace(result," ","_");
   return result;
  }

string SafeFileToken(string value)
  {
   StringTrimLeft(value);
   StringTrimRight(value);
   StringReplace(value,"\\","_");
   StringReplace(value,"/","_");
   StringReplace(value,":","_");
   StringReplace(value,"*","_");
   StringReplace(value,"?","_");
   StringReplace(value,"\"","_");
   StringReplace(value,"<","_");
   StringReplace(value,">","_");
   StringReplace(value,"|","_");
   StringReplace(value," ","_");
   return value;
  }

string CsvText(string value)
  {
   // FileWrite separates parameters but does not RFC-4180-escape delimiters
   // inside strings. Always quote source text, double embedded quotes, and
   // flatten line breaks so every exported record remains exactly one line.
   StringReplace(value,"\r"," ");
   StringReplace(value,"\n"," ");
   StringReplace(value,"\"","\"\"");
   return "\""+value+"\"";
  }

int SafeDigits(const uint digits)
  {
   if(digits>16)
      return 16;
   return (int)digits;
  }

string RawCalendarInteger(const long raw)
  {
   if(raw==LONG_MIN)
      return "";
   return IntegerToString(raw);
  }

string AdjustedCalendarValue(const long raw,const uint digits)
  {
   if(raw==LONG_MIN)
      return "";
   const double adjusted=(double)raw/1000000.0;
   return DoubleToString(adjusted,SafeDigits(digits));
  }

//+------------------------------------------------------------------+
//| Exact importance mapping                                        |
//+------------------------------------------------------------------+
string ImportanceLabel(const ENUM_CALENDAR_EVENT_IMPORTANCE importance)
  {
   switch(importance)
     {
      case CALENDAR_IMPORTANCE_NONE:     return "none";
      case CALENDAR_IMPORTANCE_LOW:      return "low";
      case CALENDAR_IMPORTANCE_MODERATE: return "medium";
      case CALENDAR_IMPORTANCE_HIGH:     return "high";
     }
   return "unknown";
  }

//+------------------------------------------------------------------+
//| CSV open helper: UTF-8, comma-delimited, isolated run folder     |
//+------------------------------------------------------------------+
int OpenCsv(const string relative_path)
  {
   ResetLastError();
   const int handle=FileOpen(g_export_root+"\\"+relative_path,
                             FILE_WRITE|FILE_CSV|FILE_ANSI|g_file_flags,
                             ',',CP_UTF8);
   if(handle==INVALID_HANDLE)
      PrintFormat("ERROR: FileOpen failed for %s (error %d)",relative_path,GetLastError());
   return handle;
  }

//+------------------------------------------------------------------+
//| Calendar API retry helpers                                      |
//+------------------------------------------------------------------+
int LoadEventsForCurrency(const string currency,MqlCalendarEvent &events[],int &last_error)
  {
   const int attempts=(int)MathMax(1,RequestRetries);
   for(int attempt=1;attempt<=attempts;attempt++)
     {
      ResetLastError();
      const int count=CalendarEventByCurrency(currency,events);
      last_error=GetLastError();
      if(count>=0)
         return count;
      PrintFormat("CalendarEventByCurrency(%s) failed: attempt %d/%d, error %d",
                  currency,attempt,attempts,last_error);
      if(attempt<attempts)
         Sleep((uint)MathMax(0,RetryDelayMilliseconds));
     }
   return -1;
  }

int LoadValuesForEvent(const ulong event_id,MqlCalendarValue &values[],int &last_error)
  {
   const int attempts=(int)MathMax(1,RequestRetries);
   for(int attempt=1;attempt<=attempts;attempt++)
     {
      ResetLastError();
      const int count=CalendarValueHistoryByEvent(event_id,values,CalendarFromDate,g_calendar_to);
      last_error=GetLastError();
      if(count>=0)
         return count;
      PrintFormat("CalendarValueHistoryByEvent(%s) failed: attempt %d/%d, error %d",
                  ULongString(event_id),attempt,attempts,last_error);
      if(attempt<attempts)
         Sleep((uint)MathMax(0,RetryDelayMilliseconds));
     }
   return -1;
  }

//+------------------------------------------------------------------+
//| Write one immutable event-definition row                         |
//+------------------------------------------------------------------+
void WriteEventRow(const int handle,
                   const string requested_currency,
                   const MqlCalendarEvent &event,
                   const MqlCalendarCountry &country,
                   const bool country_ok)
  {
   FileWrite(handle,
      ULongString(event.id),
      CsvText(requested_currency),
      ULongString(event.country_id),
      CsvText(country_ok ? country.code : ""),
      CsvText(country_ok ? country.name : ""),
      CsvText(country_ok ? country.currency : ""),
      CsvText(country_ok ? country.currency_symbol : ""),
      CsvText(country_ok ? country.url_name : ""),
      CsvText(event.name),
      CsvText(event.event_code),
      EnumToString(event.type),
      IntegerToString((int)event.type),
      EnumToString(event.sector),
      IntegerToString((int)event.sector),
      EnumToString(event.frequency),
      IntegerToString((int)event.frequency),
      EnumToString(event.time_mode),
      IntegerToString((int)event.time_mode),
      EnumToString(event.unit),
      IntegerToString((int)event.unit),
      ImportanceLabel(event.importance),
      EnumToString(event.importance),
      IntegerToString((int)event.importance),
      EnumToString(event.multiplier),
      IntegerToString((int)event.multiplier),
      IntegerToString((int)event.digits),
      CsvText(event.source_url),
      BoolString(country_ok)
   );
  }

//+------------------------------------------------------------------+
//| Write one release row. First 11 columns remain v2-compatible.   |
//+------------------------------------------------------------------+
void WriteReleaseRow(const int handle,
                     const string requested_currency,
                     const MqlCalendarEvent &event,
                     const MqlCalendarCountry &country,
                     const bool country_ok,
                     const MqlCalendarValue &value)
  {
   FileWrite(handle,
      ULongString(event.id),
      ULongString(value.id),
      Int64String((long)value.time),
      CsvText(requested_currency),
      CsvText(country_ok ? country.code : ""),
      CsvText(event.name),
      ImportanceLabel(event.importance),
      AdjustedCalendarValue(value.actual_value,event.digits),
      AdjustedCalendarValue(value.forecast_value,event.digits),
      AdjustedCalendarValue(value.prev_value,event.digits),
      AdjustedCalendarValue(value.revised_prev_value,event.digits),
      value.period>0 ? Int64String((long)value.period) : "",
      IntegerToString(value.revision),
      EnumToString(value.impact_type),
      IntegerToString((int)value.impact_type),
      ULongString(value.event_id),
      ULongString(event.country_id),
      CsvText(event.event_code),
      EnumToString(event.type),
      EnumToString(event.sector),
      EnumToString(event.frequency),
      EnumToString(event.time_mode),
      EnumToString(event.unit),
      EnumToString(event.multiplier),
      IntegerToString((int)event.digits),
      EnumToString(event.importance),
      IntegerToString((int)event.importance),
      CsvText(event.source_url),
      RawCalendarInteger(value.actual_value),
      RawCalendarInteger(value.forecast_value),
      RawCalendarInteger(value.prev_value),
      RawCalendarInteger(value.revised_prev_value),
      ServerTimeText(value.time),
      ServerTimeText(value.period),
      "trade_server_time",
      BoolString(country_ok)
   );
  }

//+------------------------------------------------------------------+
//| Economic calendar export                                        |
//+------------------------------------------------------------------+
CalendarExportResult ExportEconomicCalendar()
  {
   CalendarExportResult result;
   ZeroMemory(result);

   const int event_handle=OpenCsv("calendar_events.csv");
   const int release_handle=OpenCsv("calendar_releases.csv");
   if(event_handle==INVALID_HANDLE || release_handle==INVALID_HANDLE)
     {
      if(event_handle!=INVALID_HANDLE) FileClose(event_handle);
      if(release_handle!=INVALID_HANDLE) FileClose(release_handle);
      return result;
     }

   FileWrite(event_handle,
      "event_id","requested_currency","country_id","country_code","country_name",
      "country_currency","country_currency_symbol","country_url_name","event_name","event_code",
      "event_type","event_type_code","sector","sector_code","frequency","frequency_code",
      "time_mode","time_mode_code","unit","unit_code","importance","importance_enum",
      "importance_code","multiplier","multiplier_code","digits","source_url","country_lookup_ok"
   );

   FileWrite(release_handle,
      "event_id","value_id","timestamp","currency","country_code","event_name","importance",
      "actual","forecast","previous","revised_previous",
      "period","revision","impact_type","impact_type_code","value_event_id","country_id",
      "event_code","event_type","sector","frequency","time_mode","unit","multiplier","digits",
      "importance_enum","importance_code","source_url",
      "actual_raw_scaled_1e6","forecast_raw_scaled_1e6","previous_raw_scaled_1e6",
      "revised_previous_raw_scaled_1e6","timestamp_server_text","period_server_text",
      "timestamp_convention","country_lookup_ok"
   );

   string currencies[];
   const int currency_count=StringSplit(CalendarCurrencies,',',currencies);
   if(currency_count<=0)
     {
      Print("ERROR: CalendarCurrencies did not contain any values.");
      FileClose(event_handle);
      FileClose(release_handle);
      return result;
     }

   bool abort_export=false;
   for(int c=0;c<currency_count && !abort_export;c++)
     {
      string currency=currencies[c];
      StringTrimLeft(currency);
      StringTrimRight(currency);
      StringToUpper(currency);
      if(currency=="")
         continue;

      MqlCalendarEvent events[];
      int last_error=0;
      const int event_count=LoadEventsForCurrency(currency,events,last_error);
      if(event_count<0)
        {
         result.event_queries_failed++;
         if(StopOnCalendarError)
            abort_export=true;
         continue;
        }

      int currency_releases=0;
      for(int e=0;e<event_count;e++)
        {
         const MqlCalendarEvent event=events[e];
         MqlCalendarCountry country;
         ZeroMemory(country);
         ResetLastError();
         const bool country_ok=CalendarCountryById(event.country_id,country);
         if(!country_ok)
            result.countries_failed++;

         WriteEventRow(event_handle,currency,event,country,country_ok);
         result.events++;

         MqlCalendarValue values[];
         const int value_count=LoadValuesForEvent(event.id,values,last_error);
         if(value_count<0)
           {
            result.value_queries_failed++;
            if(StopOnCalendarError)
              {
               abort_export=true;
               break;
              }
            continue;
           }

         for(int v=0;v<value_count;v++)
           {
            if(values[v].event_id!=event.id)
               result.event_id_mismatches++;
            WriteReleaseRow(release_handle,currency,event,country,country_ok,values[v]);
            result.releases++;
            currency_releases++;
            if((result.releases%10000)==0)
               FileFlush(release_handle);
           }
        }
      PrintFormat("Calendar %s: %d event definitions, %d releases",
                  currency,event_count,currency_releases);
     }

   FileFlush(event_handle);
   FileFlush(release_handle);
   FileClose(event_handle);
   FileClose(release_handle);

   result.completed=(!abort_export &&
                     result.event_queries_failed==0 &&
                     result.value_queries_failed==0 &&
                     result.countries_failed==0 &&
                     result.event_id_mismatches==0);
   return result;
  }

//+------------------------------------------------------------------+
//| Candle helpers                                                   |
//+------------------------------------------------------------------+
int LoadRates(const string symbol,MqlRates &rates[],int &last_error)
  {
   const int attempts=(int)MathMax(1,RequestRetries);
   for(int attempt=1;attempt<=attempts;attempt++)
     {
      ResetLastError();
      const int copied=CopyRates(symbol,CandleTimeframe,CandleFromDate,g_candle_to,rates);
      last_error=GetLastError();
      if(copied>=0)
         return copied;
      PrintFormat("CopyRates(%s) failed: attempt %d/%d, error %d",
                  symbol,attempt,attempts,last_error);
      if(attempt<attempts)
         Sleep((uint)MathMax(0,RetryDelayMilliseconds));
     }
   return -1;
  }

string TimeframeToken()
  {
   string token=EnumToString(CandleTimeframe);
   StringReplace(token,"PERIOD_","");
   return token;
  }

string CanonicalSymbolToken(const string symbol)
  {
   string base=SymbolInfoString(symbol,SYMBOL_CURRENCY_BASE);
   string profit=SymbolInfoString(symbol,SYMBOL_CURRENCY_PROFIT);
   StringToUpper(base);
   StringToUpper(profit);
   if(StringLen(base)==3 && StringLen(profit)==3)
      return SafeFileToken(base+profit);
   return SafeFileToken(symbol);
  }

bool StringArrayContains(string &values[],const string target)
  {
   for(int i=0;i<ArraySize(values);i++)
      if(values[i]==target)
         return true;
   return false;
  }

void StringArrayAppend(string &values[],const string value)
  {
   const int size=ArraySize(values);
   ArrayResize(values,size+1);
   values[size]=value;
  }

//+------------------------------------------------------------------+
//| H1/selected-timeframe export                                     |
//+------------------------------------------------------------------+
CandleExportResult ExportCandles()
  {
   CandleExportResult result;
   ZeroMemory(result);

   const int manifest_handle=OpenCsv("candle_symbols.csv");
   if(manifest_handle==INVALID_HANDLE)
      return result;

   FileWrite(manifest_handle,
      "source_symbol","canonical_symbol","output_file","timeframe",
      "calculation_mode","calculation_mode_code","symbol_digits","point","currency_base","currency_profit",
      "bars_copied","bars_written","earliest_bar_timestamp",
      "latest_bar_timestamp","earliest_bar_server_text","latest_bar_server_text",
      "requested_from","requested_to","coverage_starts_after_requested","coverage_ends_before_requested",
      "excluded_incomplete_bars","copy_error","status"
   );

   const int total_symbols=SymbolsTotal(true);
   result.symbols_seen=total_symbols;
   const int period_seconds=PeriodSeconds(CandleTimeframe);
   if(period_seconds<=0)
     {
      Print("ERROR: CandleTimeframe has no valid PeriodSeconds value.");
      FileClose(manifest_handle);
      return result;
     }

   string used_output_files[];
   const string timeframe=TimeframeToken();

   for(int i=0;i<total_symbols;i++)
     {
      const string symbol=SymbolName(i,true);
      if(symbol=="")
         continue;

      const ENUM_SYMBOL_CALC_MODE calculation_mode=
         (ENUM_SYMBOL_CALC_MODE)SymbolInfoInteger(symbol,SYMBOL_TRADE_CALC_MODE);
      const bool is_forex=(calculation_mode==SYMBOL_CALC_MODE_FOREX ||
                           calculation_mode==SYMBOL_CALC_MODE_FOREX_NO_LEVERAGE);
      if(ExportOnlyForexSymbols && !is_forex)
        {
         result.symbols_skipped++;
         FileWrite(manifest_handle,
            CsvText(symbol),"","",CsvText(timeframe),
            EnumToString(calculation_mode),IntegerToString((int)calculation_mode),
            IntegerToString((int)SymbolInfoInteger(symbol,SYMBOL_DIGITS)),
            DoubleToString(SymbolInfoDouble(symbol,SYMBOL_POINT),16),
            CsvText(SymbolInfoString(symbol,SYMBOL_CURRENCY_BASE)),
            CsvText(SymbolInfoString(symbol,SYMBOL_CURRENCY_PROFIT)),
            "0","0","","","","",
            Int64String((long)CandleFromDate),Int64String((long)g_candle_to),
            "","","0","0","skipped_non_forex"
         );
         continue;
        }

      const string canonical=CanonicalSymbolToken(symbol);
      string output_file="candles\\candles_"+canonical+"_"+timeframe+".csv";
      if(StringArrayContains(used_output_files,output_file))
         output_file="candles\\candles_"+canonical+"_"+IntegerToString(i)+"_"+timeframe+".csv";
      StringArrayAppend(used_output_files,output_file);

      MqlRates rates[];
      ArraySetAsSeries(rates,false);
      int copy_error=0;
      const int copied=LoadRates(symbol,rates,copy_error);
      if(copied<=0)
        {
         result.symbols_failed++;
         FileWrite(manifest_handle,
            CsvText(symbol),CsvText(canonical),CsvText(output_file),CsvText(timeframe),
            EnumToString(calculation_mode),IntegerToString((int)calculation_mode),
            IntegerToString((int)SymbolInfoInteger(symbol,SYMBOL_DIGITS)),
            DoubleToString(SymbolInfoDouble(symbol,SYMBOL_POINT),16),
            CsvText(SymbolInfoString(symbol,SYMBOL_CURRENCY_BASE)),
            CsvText(SymbolInfoString(symbol,SYMBOL_CURRENCY_PROFIT)),
            IntegerToString(MathMax(0,copied)),"0","","","","",
            Int64String((long)CandleFromDate),Int64String((long)g_candle_to),
            "","","0",IntegerToString(copy_error),copied<0 ? "copy_failed" : "no_bars"
         );
         continue;
        }

      const int candle_handle=OpenCsv(output_file);
      if(candle_handle==INVALID_HANDLE)
        {
         result.symbols_failed++;
         FileWrite(manifest_handle,
            CsvText(symbol),CsvText(canonical),CsvText(output_file),CsvText(timeframe),
            EnumToString(calculation_mode),IntegerToString((int)calculation_mode),
            IntegerToString((int)SymbolInfoInteger(symbol,SYMBOL_DIGITS)),
            DoubleToString(SymbolInfoDouble(symbol,SYMBOL_POINT),16),
            CsvText(SymbolInfoString(symbol,SYMBOL_CURRENCY_BASE)),
            CsvText(SymbolInfoString(symbol,SYMBOL_CURRENCY_PROFIT)),
            IntegerToString(copied),"0","","","","",
            Int64String((long)CandleFromDate),Int64String((long)g_candle_to),
            "","","0",IntegerToString(GetLastError()),"file_open_failed"
         );
         continue;
        }

      FileWrite(candle_handle,
         "time","open","high","low","close","tick_volume","spread","real_volume",
         "source_symbol","time_server_text","timestamp_convention","complete_at_export"
      );

      const int digits=(int)SymbolInfoInteger(symbol,SYMBOL_DIGITS);
      int written=0;
      int excluded=0;
      datetime earliest=0;
      datetime latest=0;

      for(int b=0;b<copied;b++)
        {
         const bool complete_at_snapshot=((long)rates[b].time+(long)period_seconds<=(long)g_snapshot_server);
         const bool complete_in_request=((long)rates[b].time+(long)period_seconds<=(long)g_candle_to);
         if(ExcludeIncompleteBar && (!complete_at_snapshot || !complete_in_request))
           {
            excluded++;
            continue;
           }

         FileWrite(candle_handle,
            Int64String((long)rates[b].time),
            DoubleToString(rates[b].open,digits),
            DoubleToString(rates[b].high,digits),
            DoubleToString(rates[b].low,digits),
            DoubleToString(rates[b].close,digits),
            Int64String(rates[b].tick_volume),
            IntegerToString(rates[b].spread),
            Int64String(rates[b].real_volume),
            CsvText(symbol),
            ServerTimeText(rates[b].time),
            "trade_server_time",
            BoolString(complete_at_snapshot)
         );
         if(written==0)
            earliest=rates[b].time;
         latest=rates[b].time;
         written++;
         if((written%10000)==0)
            FileFlush(candle_handle);
        }

      FileFlush(candle_handle);
      FileClose(candle_handle);

      const bool starts_late=(written>0 && earliest>CandleFromDate+(datetime)period_seconds);
      const bool ends_early=(written>0 && latest+(datetime)period_seconds<g_candle_to-(datetime)period_seconds);
      FileWrite(manifest_handle,
         CsvText(symbol),CsvText(canonical),CsvText(output_file),CsvText(timeframe),
         EnumToString(calculation_mode),IntegerToString((int)calculation_mode),IntegerToString(digits),
         DoubleToString(SymbolInfoDouble(symbol,SYMBOL_POINT),digits),
         CsvText(SymbolInfoString(symbol,SYMBOL_CURRENCY_BASE)),
         CsvText(SymbolInfoString(symbol,SYMBOL_CURRENCY_PROFIT)),
         IntegerToString(copied),IntegerToString(written),
         written>0 ? Int64String((long)earliest) : "",
         written>0 ? Int64String((long)latest) : "",
         ServerTimeText(earliest),ServerTimeText(latest),
         Int64String((long)CandleFromDate),Int64String((long)g_candle_to),
         BoolString(starts_late),BoolString(ends_early),IntegerToString(excluded),
         IntegerToString(copy_error),written>0 ? "ok" : "no_complete_bars"
      );

      if(written>0)
        {
         result.symbols_exported++;
         result.bars_exported+=(long)written;
        }
      else
         result.symbols_failed++;

      PrintFormat("Candles %s -> %s: copied %d, wrote %d, excluded %d",
                  symbol,output_file,copied,written,excluded);
     }

   FileFlush(manifest_handle);
   FileClose(manifest_handle);
   result.completed=(result.symbols_failed==0);
   return result;
  }

//+------------------------------------------------------------------+
//| Key/value provenance manifest                                   |
//+------------------------------------------------------------------+
void ManifestRow(const int handle,const string key,const string value,const string note="")
  {
   FileWrite(handle,CsvText(key),CsvText(value),CsvText(note));
  }

void WriteManifest(const CalendarExportResult &calendar_result,
                   const CandleExportResult &candle_result,
                   const uint elapsed_ms)
  {
   const int handle=OpenCsv("manifest.csv");
   if(handle==INVALID_HANDLE)
      return;

   FileWrite(handle,"key","value","note");
   ManifestRow(handle,"schema_version",SCHEMA_VERSION);
   ManifestRow(handle,"exporter_version",EXPORTER_VERSION);
   ManifestRow(handle,"csv_text_encoding","RFC4180-style quoted UTF-8",
               "Embedded quotes are doubled and source line breaks are flattened to preserve one record per line.");
   ManifestRow(handle,"export_id",g_export_id);
   ManifestRow(handle,"export_root",g_export_root);
   ManifestRow(handle,"completed_elapsed_ms",IntegerToString((int)elapsed_ms));
   ManifestRow(handle,"snapshot_trade_server_timestamp",Int64String((long)g_snapshot_server));
   ManifestRow(handle,"snapshot_trade_server_text",ServerTimeText(g_snapshot_server));
   ManifestRow(handle,"snapshot_gmt_timestamp",Int64String((long)g_snapshot_gmt));
   ManifestRow(handle,"snapshot_gmt_text",TimeToString(g_snapshot_gmt,TIME_DATE|TIME_SECONDS));
   const long raw_offset=(long)g_snapshot_server-(long)g_snapshot_gmt;
   const long rounded_offset=(long)MathRound((double)raw_offset/60.0)*60;
   ManifestRow(handle,"trade_server_minus_gmt_seconds_snapshot",Int64String(rounded_offset),
               "Snapshot estimate only; retain timestamps as trade-server time and do not assume a fixed DST offset.");
   ManifestRow(handle,"timestamp_convention","trade_server_time",
               "MT5 calendar and bar timestamps are exported without UTC conversion.");

   ManifestRow(handle,"terminal_connected",BoolString((bool)TerminalInfoInteger(TERMINAL_CONNECTED)));
   ManifestRow(handle,"terminal_company",TerminalInfoString(TERMINAL_COMPANY));
   ManifestRow(handle,"terminal_name",TerminalInfoString(TERMINAL_NAME));
   ManifestRow(handle,"terminal_language",TerminalInfoString(TERMINAL_LANGUAGE));
   ManifestRow(handle,"terminal_build",IntegerToString((int)TerminalInfoInteger(TERMINAL_BUILD)));
   ManifestRow(handle,"terminal_max_bars",IntegerToString((int)TerminalInfoInteger(TERMINAL_MAXBARS)),
               "A low terminal Max bars setting can truncate requested candle history.");
   ManifestRow(handle,"account_company",AccountInfoString(ACCOUNT_COMPANY));
   ManifestRow(handle,"account_server",AccountInfoString(ACCOUNT_SERVER));
   ManifestRow(handle,"privacy_note","Account login and client name intentionally not exported.");

   ManifestRow(handle,"save_to_common_folder",BoolString(SaveToCommonFolder));
   ManifestRow(handle,"storage_scope",SaveToCommonFolder ? "Terminal/Common/Files" : "Terminal/MQL5/Files");
   ManifestRow(handle,"export_calendar",BoolString(ExportCalendar));
   ManifestRow(handle,"calendar_currencies",CalendarCurrencies);
   ManifestRow(handle,"calendar_from_timestamp",Int64String((long)CalendarFromDate));
   ManifestRow(handle,"calendar_from_server_text",ServerTimeText(CalendarFromDate));
   ManifestRow(handle,"calendar_to_timestamp",Int64String((long)g_calendar_to));
   ManifestRow(handle,"calendar_to_server_text",ServerTimeText(g_calendar_to));
   ManifestRow(handle,"calendar_events_exported",IntegerToString(calendar_result.events));
   ManifestRow(handle,"calendar_releases_exported",IntegerToString(calendar_result.releases));
   ManifestRow(handle,"calendar_country_lookup_failures",IntegerToString(calendar_result.countries_failed));
   ManifestRow(handle,"calendar_event_query_failures",IntegerToString(calendar_result.event_queries_failed));
   ManifestRow(handle,"calendar_value_query_failures",IntegerToString(calendar_result.value_queries_failed));
   ManifestRow(handle,"calendar_event_id_mismatches",IntegerToString(calendar_result.event_id_mismatches));
   ManifestRow(handle,"calendar_completed",BoolString(calendar_result.completed));

   ManifestRow(handle,"export_market_watch_bars",BoolString(ExportMarketWatchBars));
   ManifestRow(handle,"candle_timeframe",EnumToString(CandleTimeframe));
   ManifestRow(handle,"candle_from_timestamp",Int64String((long)CandleFromDate));
   ManifestRow(handle,"candle_from_server_text",ServerTimeText(CandleFromDate));
   ManifestRow(handle,"candle_to_timestamp",Int64String((long)g_candle_to));
   ManifestRow(handle,"candle_to_server_text",ServerTimeText(g_candle_to));
   ManifestRow(handle,"exclude_incomplete_bar",BoolString(ExcludeIncompleteBar));
   ManifestRow(handle,"export_only_forex_symbols",BoolString(ExportOnlyForexSymbols),
               "Uses SYMBOL_TRADE_CALC_MODE and accepts FOREX and FOREX_NO_LEVERAGE modes.");
   ManifestRow(handle,"market_watch_symbols_seen",IntegerToString(candle_result.symbols_seen));
   ManifestRow(handle,"market_watch_symbols_skipped_non_forex",IntegerToString(candle_result.symbols_skipped));
   ManifestRow(handle,"candle_symbols_exported",IntegerToString(candle_result.symbols_exported));
   ManifestRow(handle,"candle_symbols_failed",IntegerToString(candle_result.symbols_failed));
   ManifestRow(handle,"candle_bars_exported",Int64String(candle_result.bars_exported));
   ManifestRow(handle,"candles_completed",BoolString(candle_result.completed));
   ManifestRow(handle,"request_retries",IntegerToString(RequestRetries));
   ManifestRow(handle,"retry_delay_milliseconds",IntegerToString(RetryDelayMilliseconds));
   ManifestRow(handle,"stop_on_calendar_error",BoolString(StopOnCalendarError));
   ManifestRow(handle,"checksum_note","Compute SHA-256 for every output file immediately after copying the folder from MT5.");

   FileFlush(handle);
   FileClose(handle);
  }

//+------------------------------------------------------------------+
//| Script entry point                                               |
//+------------------------------------------------------------------+
void OnStart()
  {
   Print("==================================================================");
   Print(" FYODOR RESEARCH EXPORTER v3 - PROVENANCE-PRESERVING EXPORT");
   Print("==================================================================");

   if(!TerminalInfoInteger(TERMINAL_CONNECTED))
     {
      const string error="MT5 is not connected to a trade server. Export aborted.";
      Print("ERROR: "+error);
      if(ShowCompletionDialog)
         MessageBox(error,"Fyodor Research Exporter",MB_OK|MB_ICONERROR);
      return;
     }

   g_snapshot_server=TimeTradeServer();
   g_snapshot_gmt=TimeGMT();
   if(g_snapshot_server<=0)
     {
      const string error="TimeTradeServer returned an invalid snapshot time. Export aborted.";
      Print("ERROR: "+error);
      if(ShowCompletionDialog)
         MessageBox(error,"Fyodor Research Exporter",MB_OK|MB_ICONERROR);
      return;
     }

   g_calendar_to=(CalendarToDate>0 ? CalendarToDate : g_snapshot_server);
   g_candle_to=(CandleToDate>0 ? CandleToDate : g_snapshot_server);
   if((ExportCalendar && CalendarFromDate>=g_calendar_to) ||
      (ExportMarketWatchBars && CandleFromDate>=g_candle_to))
     {
      const string error="An export start date is not earlier than its resolved end date.";
      Print("ERROR: "+error);
      if(ShowCompletionDialog)
         MessageBox(error,"Fyodor Research Exporter",MB_OK|MB_ICONERROR);
      return;
     }

   g_export_id=CompactTimestamp(g_snapshot_server);
   g_export_root=SafeFileToken(OutputRootPrefix)+"_"+g_export_id+"_server";
   g_file_flags=SaveToCommonFolder ? FILE_COMMON : 0;

   const uint started=GetTickCount();
   CalendarExportResult calendar_result;
   CandleExportResult candle_result;
   ZeroMemory(calendar_result);
   ZeroMemory(candle_result);

   if(ExportCalendar)
      calendar_result=ExportEconomicCalendar();
   else
      calendar_result.completed=true;

   if(ExportMarketWatchBars)
      candle_result=ExportCandles();
   else
      candle_result.completed=true;

   const uint elapsed=GetTickCount()-started;
   WriteManifest(calendar_result,candle_result,elapsed);

   const bool success=calendar_result.completed && candle_result.completed;
   Print("==================================================================");
   PrintFormat(" Export folder: %s",g_export_root);
   PrintFormat(" Calendar: %d events, %d releases, complete=%s",
               calendar_result.events,calendar_result.releases,BoolString(calendar_result.completed));
   PrintFormat(" Candles: %d symbols, %s bars, complete=%s",
               candle_result.symbols_exported,Int64String(candle_result.bars_exported),BoolString(candle_result.completed));
   PrintFormat(" Elapsed: %.1f seconds",(double)elapsed/1000.0);
   Print(" Copy the ENTIRE export folder without renaming or editing files.");
   Print("==================================================================");

   if(ShowCompletionDialog)
     {
      const string message=StringFormat(
         "Export %s\n\nFolder: %s\nCalendar releases: %d\nCandle symbols: %d\nCandle bars: %s\n\nCopy the entire folder unchanged.",
         success ? "completed" : "completed with warnings",g_export_root,
         calendar_result.releases,candle_result.symbols_exported,Int64String(candle_result.bars_exported));
      MessageBox(message,"Fyodor Research Exporter v3",MB_OK|(success ? MB_ICONINFORMATION : MB_ICONWARNING));
     }
  }
//+------------------------------------------------------------------+
