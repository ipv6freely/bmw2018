# bmw2018

1) Gets token from BMW API
2) Uses token to get battery information for a specific VIN
3) Compares battery % to previous %, if saved
4) If battery is 100% and last reading was less than 100% (to prevent multiple "hits"), send SMS via AWS
5) If battery is 100% and last reading was 100%, do nothing
6) Also send SMS via AWS if mileage hits 40mi available (just enough for me to get home from work)

Hope this is useful. 
