# Duplicati Backup Exporter

## Duplicati Setup

For each backup you would like to monitor, update the options tab add the following "advanced" post steps:

```
send-http-result-output-format = json
send-http-url = http://YOUREXPORTER:PORT/report
```


## Prometheus Setup

```
  - job_name: "duplicati"
    scrape_interval: 60s
    metrics_path: /metrics
    static_configs:
      - targets: ['dup_exporter:80']
```


## Docker

### Build Instruction

> docker build . -t mrflobow/duplicati_exporter:0.1 --platform linux/amd64
