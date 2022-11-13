# Duplicati Backup Exporter

## Duplicati Setup

For each backup you would like to monitor, update the options tab add the following "advanced" post steps:

```
send-http-result-output-format = json
send-http-url = http://YOUREXPORTER:PORT/report
```


## More