# SRV Truth Report

- Generated: 2026-02-15T05:20:35+05:00
- Root: /home/munaim/srv
- Artifacts: /home/munaim/srv/ops/truth_audit/20260215_051352

## Canonical paths (as detected)

- Caddy (srv): `/home/munaim/srv/proxy/caddy/Caddyfile`  ✅
- Caddy (etc): `/etc/caddy/Caddyfile`  ✅

## Executive truth summary

- This report is **read-only** inventory + probes.
- Any FAIL in probes usually indicates **path mismatch, auth mismatch, CORS mismatch, upstream down, or DNS/TLS issue**.

## Domains discovered

Parsed from Caddyfile + known:

```
127.0.0.1:13000
127.0.0.1:18000
127.0.0.1:18001
127.0.0.1:8010
127.0.0.1:8011
127.0.0.1:8012
127.0.0.1:8014
127.0.0.1:8015
127.0.0.1:8016
127.0.0.1:8025
127.0.0.1:8080
127.0.0.1:8081
127.0.0.1:8082
api.consult.alshifalab.pk
api.lims.alshifalab.pk
api.mediq.alshifalab.pk
api.ops.alshifalab.pk
api.pgsims.alshifalab.pk
api.pgsims.pmc.edu.pk
api.phc.alshifalab.pk
api.rims.alshifalab.pk
api.sims.alshifalab.pk
api.sims.pmc.edu.pk
api.sos.alshifalab.pk
consult.alshifalab.pk
dashboard.alshifalab.pk
grafana.alshifalab.pk
lims.alshifalab.pk
mediq.alshifalab.pk
ops.alshifalab.pk
pgsims.alshifalab.pk
pgsims.pmc.edu.pk
phc.alshifalab.pk
portal.alshifalab.pk
rims.alshifalab.pk
sims.alshifalab.pk
sims.pmc.edu.pk
sos.alshifalab.pk
```

## Upstreams discovered

```
127.0.0.1:13000
127.0.0.1:18000
127.0.0.1:18001
127.0.0.1:3025
127.0.0.1:8010
127.0.0.1:8011
127.0.0.1:8012
127.0.0.1:8014
127.0.0.1:8015
127.0.0.1:8016
127.0.0.1:8025
127.0.0.1:8080
127.0.0.1:8081
127.0.0.1:8082
```

## Docker inventory (top)

### docker inventory snapshot

```
### docker version
Client: Docker Engine - Community
 Version:           29.2.1
 API version:       1.53
 Go version:        go1.25.6
 Git commit:        a5c7197
 Built:             Mon Feb  2 17:17:26 2026
 OS/Arch:           linux/amd64
 Context:           default

Server: Docker Engine - Community
 Engine:
  Version:          29.2.1
  API version:      1.53 (minimum version 1.44)
  Go version:       go1.25.6
  Git commit:       6bc6209
  Built:            Mon Feb  2 17:17:26 2026
  OS/Arch:          linux/amd64
  Experimental:     false
 containerd:
  Version:          v2.2.1
  GitCommit:        dea7da592f5d1d2b7755e3a161be07f43fad8f75
 runc:
  Version:          1.3.4
  GitCommit:        v1.3.4-0-gd6d73eb8
 docker-init:
  Version:          0.19.0
  GitCommit:        de40ad0

### docker info (trimmed)
Client: Docker Engine - Community
 Version:    29.2.1
 Context:    default
 Debug Mode: false
 Plugins:
  buildx: Docker Buildx (Docker Inc.)
    Version:  v0.31.1
    Path:     /usr/libexec/docker/cli-plugins/docker-buildx
  compose: Docker Compose (Docker Inc.)
    Version:  v5.0.2
    Path:     /usr/libexec/docker/cli-plugins/docker-compose
  model: Docker Model Runner (Docker Inc.)
    Version:  v1.0.12
    Path:     /usr/libexec/docker/cli-plugins/docker-model

Server:
 Containers: 8
  Running: 8
  Paused: 0
  Stopped: 0
 Images: 8
 Server Version: 29.2.1
 Storage Driver: overlayfs
  driver-type: io.containerd.snapshotter.v1
 Logging Driver: json-file
 Cgroup Driver: systemd
 Cgroup Version: 2
 Plugins:
  Volume: local
  Network: bridge host ipvlan macvlan null overlay
  Log: awslogs fluentd gcplogs gelf journald json-file local splunk syslog
 CDI spec directories:
  /etc/cdi
  /var/run/cdi
 Swarm: inactive
 Runtimes: io.containerd.runc.v2 runc
 Default Runtime: runc
 Init Binary: docker-init
 containerd version: dea7da592f5d1d2b7755e3a161be07f43fad8f75
 runc version: v1.3.4-0-gd6d73eb8
 init version: de40ad0
 Security Options:
  apparmor
  seccomp
   Profile: builtin
  cgroupns
 Kernel Version: 6.14.0-1021-gcp
 Operating System: Ubuntu 24.04.4 LTS
 OSType: linux
 Architecture: x86_64
 CPUs: 4
 Total Memory: 21.5GiB
 Name: vps.us-central1-f.c.munaimfinance.internal
 ID: a3397c38-e049-483a-ab32-af2e4ce74123
 Docker Root Dir: /var/lib/docker
 Debug Mode: false
 Experimental: false
 Insecure Registries:
  127.0.0.0/8
  ::1/128
 Live Restore Enabled: false
 Firewall Backend: iptables


### containers (ps -a)
CONTAINER ID                                                       IMAGE                          COMMAND                                                                                     CREATED          STATUS                    PORTS                                                NAMES
9a5db015b83d5e973bda45d52c0742ff1b900f1f906885960d734203ca7eba22   lims-celery                    "celery -A config worker -l INFO --concurrency=4"                                           6 minutes ago    Up 6 minutes              8000/tcp                                             lims_celery
a78a8dc863c6b6092828c2f9e4d8ae0c21ae9b8b64019cb3207af82130bc8664   lims-backend                   "/app/bootstrap_prod.sh gunicorn --bind 0.0.0.0:8000 --workers 4 config.wsgi:application"   6 minutes ago    Up 6 minutes (healthy)    8000/tcp                                             lims_backend
7eee62ca3c01d5699684f5fe7be59a65570b46e05c1362efc6ff1764894c2914   caddy:2-alpine                 "caddy run --config /etc/caddy/Caddyfile --adapter caddyfile"                               30 minutes ago   Up 30 minutes (healthy)   443/tcp, 2019/tcp, 443/udp, 127.0.0.1:8012->80/tcp   lims_proxy
951278ef03b4deae5be97011b53011b2b1cb598f49988bf84dad08fc19025400   lims-frontend                  "/docker-entrypoint.sh nginx -g 'daemon off;'"                                              30 minutes ago   Up 30 minutes             80/tcp                                               lims_frontend
b4a4d7d428a193b6a8c40127755d7a7eda453c625d7b2e998e6fdc892e755522   dashboard-dashboard_frontend   "/docker-entrypoint.sh nginx -g 'daemon off;'"                                              31 minutes ago   Up 31 minutes             127.0.0.1:8013->80/tcp                               dashboard_frontend
38dc6704f9a367d32dd3e0e74b5fad31795df5e1ab3b55621c8e7063c0572a3b   dashboard-dashboard_backend    "uvicorn app.main:app --host 0.0.0.0 --port 8000"                                           31 minutes ago   Up 31 minutes             8000/tcp                                             dashboard_backend
0404f8cb8cbb5d03131500f2e58ecb929626cf6e7a7e4fa4d02bd17cfaa83ac9   postgres:16-alpine             "docker-entrypoint.sh postgres"                                                             31 minutes ago   Up 31 minutes (healthy)   5432/tcp                                             lims_db
55e7040bc6a4d1fe24af30bf2daafa884848abc8e51baf32fee6b65778fe27ff   redis:7-alpine                 "docker-entrypoint.sh redis-server --appendonly yes --requirepass "                         31 minutes ago   Up 31 minutes (healthy)   6379/tcp                                             lims_redis

### containers (formatted)
NAMES                STATUS                    PORTS                                                IMAGE
lims_celery          Up 6 minutes              8000/tcp                                             lims-celery
lims_backend         Up 6 minutes (healthy)    8000/tcp                                             lims-backend
lims_proxy           Up 30 minutes (healthy)   443/tcp, 2019/tcp, 443/udp, 127.0.0.1:8012->80/tcp   caddy:2-alpine
lims_frontend        Up 30 minutes             80/tcp                                               lims-frontend
dashboard_frontend   Up 31 minutes             127.0.0.1:8013->80/tcp                               dashboard-dashboard_frontend
dashboard_backend    Up 31 minutes             8000/tcp                                             dashboard-dashboard_backend
lims_db              Up 31 minutes (healthy)   5432/tcp                                             postgres:16-alpine
lims_redis           Up 31 minutes (healthy)   6379/tcp                                             redis:7-alpine

### images
REPOSITORY                     TAG         DIGEST                                                                    IMAGE ID       CREATED          SIZE
lims-celery                    latest      sha256:81377a2c4141ea982d5dee7d4ff17fc1e3df568baa111507d36f1105260bfdfa   81377a2c4141   7 minutes ago    1.85GB
lims-backend                   latest      sha256:6c3ca530fccb1337c5c9cca0e024f3e048a4d5266ed0efdf1937b3736d7402cf   6c3ca530fccb   9 minutes ago    1.85GB
dashboard-dashboard_backend    latest      sha256:862c2f0e04360c0860858dda952416bfbd42485c0c705754334d55c995863370   862c2f0e0436   31 minutes ago   240MB
dashboard-dashboard_frontend   latest      sha256:8bc033be69b46faf44247283fb9c8ee0efe6f3c2fa0a18c6fc06617d2b910315   8bc033be69b4   31 minutes ago   73.9MB
lims-frontend                  latest      sha256:1696c3a992bf6e7be4d6168506d67ec5554958332f355c3d58a6722b573bf831   1696c3a992bf   31 minutes ago   93.5MB
postgres                       16-alpine   sha256:97ff59a4e30e08d1c11bdcd9455e7832368c0572b576c9092cde2df4ae5552a3   97ff59a4e30e   2 days ago       395MB
caddy                          2-alpine    sha256:4c6e91c6ed0e2fa03efd5b44747b625fec79bc9cd06ac5235a779726618e530d   4c6e91c6ed0e   3 days ago       83.2MB
redis                          7-alpine    sha256:02f2cc4882f8bf87c79a220ac958f58c700bdec0dfb9b9ea61b62fb0e8f1bfcf   02f2cc4882f8   2 weeks ago      61.2MB

### volumes
DRIVER    VOLUME NAME
local     lims_caddy_config
local     lims_caddy_data
local     lims_pgdata
local     lims_redis_data
local     lims_static_files

### networks
NETWORK ID     NAME                DRIVER    SCOPE
0afc38fb011a   bridge              bridge    local
a6a8c410d8f6   dashboard_default   bridge    local
c1319ff4c7b0   host                host      local
9185764880fa   lims_network        bridge    local
fffa42f41109   none                null      local
```


## Caddy service + recent logs (top)

### caddy status + logs

```
### Caddy service status
● caddy.service - Caddy
     Loaded: loaded (/usr/lib/systemd/system/caddy.service; enabled; preset: enabled)
    Drop-In: /etc/systemd/system/caddy.service.d
             └─override.conf
     Active: active (running) since Sun 2026-02-15 04:35:31 PKT; 38min ago
       Docs: https://caddyserver.com/docs/
   Main PID: 688 (caddy)
      Tasks: 14 (limit: 26339)
     Memory: 60.9M (peak: 61.8M)
        CPU: 2.216s
     CGroup: /system.slice/caddy.service
             └─688 /usr/bin/caddy run --environ --config /etc/caddy/Caddyfile

Feb 15 04:35:22 vps caddy[688]: JOURNAL_STREAM=9:5726
Feb 15 04:35:22 vps caddy[688]: SYSTEMD_EXEC_PID=688
Feb 15 04:35:22 vps caddy[688]: MEMORY_PRESSURE_WATCH=/sys/fs/cgroup/system.slice/caddy.service/memory.pressure
Feb 15 04:35:22 vps caddy[688]: MEMORY_PRESSURE_WRITE=c29tZSAyMDAwMDAgMjAwMDAwMAA=
Feb 15 04:35:22 vps caddy[688]: {"level":"info","ts":1771112122.0152771,"msg":"using config from file","file":"/etc/caddy/Caddyfile"}
Feb 15 04:35:22 vps caddy[688]: {"level":"info","ts":1771112122.0369816,"msg":"adapted config to JSON","adapter":"caddyfile"}
Feb 15 04:35:22 vps caddy[688]: {"level":"warn","ts":1771112122.037015,"msg":"Caddyfile input is not formatted; run 'caddy fmt --overwrite' to fix inconsistencies","adapter":"caddyfile","file":"/etc/caddy/Caddyfile","line":455}
Feb 15 04:35:22 vps caddy[688]: {"level":"info","ts":1771112122.045322,"msg":"redirected default logger","from":"stderr","to":"/home/munaim/srv/proxy/caddy/logs/error.log"}
Feb 15 04:35:22 vps caddy[688]: {"level":"info","ts":1771112122.1317675,"msg":"serving initial configuration"}
Feb 15 04:35:31 vps systemd[1]: Started caddy.service - Caddy.

### Caddy recent logs (last 200 lines)
Feb 13 16:41:01 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Reloading caddy.service - Caddy...
Feb 13 16:41:01 vps.us-central1-f.c.munaimfinance.internal caddy[454781]: {"level":"info","ts":1770982861.5264854,"msg":"using config from file","file":"/etc/caddy/Caddyfile"}
Feb 13 16:41:01 vps.us-central1-f.c.munaimfinance.internal caddy[454781]: {"level":"info","ts":1770982861.5401618,"msg":"adapted config to JSON","adapter":"caddyfile"}
Feb 13 16:41:01 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Reloaded caddy.service - Caddy.
Feb 13 17:25:10 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Reloading caddy.service - Caddy...
Feb 13 17:25:10 vps.us-central1-f.c.munaimfinance.internal caddy[570879]: {"level":"info","ts":1770985510.8392475,"msg":"using config from file","file":"/etc/caddy/Caddyfile"}
Feb 13 17:25:10 vps.us-central1-f.c.munaimfinance.internal caddy[570879]: {"level":"info","ts":1770985510.8558798,"msg":"adapted config to JSON","adapter":"caddyfile"}
Feb 13 17:25:10 vps.us-central1-f.c.munaimfinance.internal caddy[570879]: {"level":"warn","ts":1770985510.855926,"msg":"Caddyfile input is not formatted; run 'caddy fmt --overwrite' to fix inconsistencies","adapter":"caddyfile","file":"/etc/caddy/Caddyfile","line":388}
Feb 13 17:25:10 vps.us-central1-f.c.munaimfinance.internal caddy[570879]: Error: sending configuration to instance: caddy responded with error: HTTP 400: {"error":"loading config: loading new config: setting up custom log 'log18': opening log writer using &logging.FileWriter{Filename:\"/var/log/caddy/mediq.log\", Mode:0x0, Roll:(*bool)(nil), RollSizeMB:0, RollCompress:(*bool)(nil), RollLocalTime:false, RollKeep:0, RollKeepDays:0}: open /var/log/caddy/mediq.log: permission denied"}
Feb 13 17:25:10 vps.us-central1-f.c.munaimfinance.internal systemd[1]: caddy.service: Control process exited, code=exited, status=1/FAILURE
Feb 13 17:26:40 vps.us-central1-f.c.munaimfinance.internal systemd[1]: caddy.service: Reload operation timed out. Killing reload process.
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal systemd[1]: caddy.service: Deactivated successfully.
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Stopped caddy.service - Caddy.
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal systemd[1]: caddy.service: Consumed 10.875s CPU time, 74.3M memory peak, 0B memory swap peak.
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Starting caddy.service - Caddy...
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: {"level":"info","ts":1770985633.2481313,"msg":"maxprocs: Leaving GOMAXPROCS=4: CPU quota undefined"}
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: {"level":"info","ts":1770985633.2492034,"msg":"GOMEMLIMIT is updated","package":"github.com/KimMachineGun/automemlimit/memlimit","GOMEMLIMIT":20775451852,"previous":9223372036854775807}
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: caddy.HomeDir=/var/lib/caddy
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: caddy.AppDataDir=/var/lib/caddy/.local/share/caddy
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: caddy.AppConfigDir=/var/lib/caddy/.config/caddy
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: caddy.ConfigAutosavePath=/var/lib/caddy/.config/caddy/autosave.json
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: caddy.Version=v2.10.2 h1:g/gTYjGMD0dec+UgMw8SnfmJ3I9+M2TdvoRL/Ovu6U8=
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: runtime.GOOS=linux
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: runtime.GOARCH=amd64
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: runtime.Compiler=gc
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: runtime.NumCPU=4
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: runtime.GOMAXPROCS=4
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: runtime.Version=go1.25.0
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: os.Getwd=/
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: LANG=C.UTF-8
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/snap/bin
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: NOTIFY_SOCKET=/run/systemd/notify
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: USER=caddy
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: LOGNAME=caddy
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: HOME=/var/lib/caddy
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: INVOCATION_ID=8025e028615743a2acc6b71cfc06e165
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: JOURNAL_STREAM=9:2718121
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: SYSTEMD_EXEC_PID=576821
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: MEMORY_PRESSURE_WATCH=/sys/fs/cgroup/system.slice/caddy.service/memory.pressure
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: MEMORY_PRESSURE_WRITE=c29tZSAyMDAwMDAgMjAwMDAwMAA=
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: {"level":"info","ts":1770985633.2493584,"msg":"using config from file","file":"/etc/caddy/Caddyfile"}
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: {"level":"info","ts":1770985633.2656786,"msg":"adapted config to JSON","adapter":"caddyfile"}
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: {"level":"warn","ts":1770985633.2657125,"msg":"Caddyfile input is not formatted; run 'caddy fmt --overwrite' to fix inconsistencies","adapter":"caddyfile","file":"/etc/caddy/Caddyfile","line":388}
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: {"level":"info","ts":1770985633.2706876,"msg":"redirected default logger","from":"stderr","to":"/home/munaim/srv/proxy/caddy/logs/error.log"}
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: {"level":"info","ts":1770985633.313658,"msg":"serving initial configuration"}
Feb 13 17:27:13 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Started caddy.service - Caddy.
Feb 13 17:28:10 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Reloading caddy.service - Caddy...
Feb 13 17:28:10 vps.us-central1-f.c.munaimfinance.internal caddy[580392]: {"level":"info","ts":1770985690.9218457,"msg":"using config from file","file":"/etc/caddy/Caddyfile"}
Feb 13 17:28:10 vps.us-central1-f.c.munaimfinance.internal caddy[580392]: {"level":"info","ts":1770985690.9332004,"msg":"adapted config to JSON","adapter":"caddyfile"}
Feb 13 17:28:10 vps.us-central1-f.c.munaimfinance.internal caddy[580392]: {"level":"warn","ts":1770985690.9332206,"msg":"Caddyfile input is not formatted; run 'caddy fmt --overwrite' to fix inconsistencies","adapter":"caddyfile","file":"/etc/caddy/Caddyfile","line":388}
Feb 13 17:28:10 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Reloaded caddy.service - Caddy.
Feb 13 23:05:10 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: 1.771005910111947e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_api.pgsims.pmc.edu.pk.lock)
Feb 13 23:05:10 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: 1.771005910111947e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_sims.pmc.edu.pk.lock)
Feb 13 23:05:20 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: 1.771005920122087e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_api.sos.alshifalab.pk.lock)
Feb 13 23:05:35 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: 1.7710059351374018e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_api.sims.pmc.edu.pk.lock)
Feb 13 23:05:50 vps.us-central1-f.c.munaimfinance.internal caddy[576821]: 1.7710059501564784e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_pgsims.pmc.edu.pk.lock)
Feb 14 00:00:01 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Reloading caddy.service - Caddy...
Feb 14 00:00:01 vps.us-central1-f.c.munaimfinance.internal caddy[1290631]: {"level":"info","ts":1771009201.9925075,"msg":"using config from file","file":"/etc/caddy/Caddyfile"}
Feb 14 00:00:02 vps.us-central1-f.c.munaimfinance.internal caddy[1290631]: {"level":"info","ts":1771009202.0037835,"msg":"adapted config to JSON","adapter":"caddyfile"}
Feb 14 00:00:02 vps.us-central1-f.c.munaimfinance.internal caddy[1290631]: {"level":"warn","ts":1771009202.003804,"msg":"Caddyfile input is not formatted; run 'caddy fmt --overwrite' to fix inconsistencies","adapter":"caddyfile","file":"/etc/caddy/Caddyfile","line":388}
Feb 14 00:00:02 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Reloaded caddy.service - Caddy.
Feb 14 00:22:40 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Stopping caddy.service - Caddy...
Feb 14 00:22:40 vps.us-central1-f.c.munaimfinance.internal systemd[1]: caddy.service: Deactivated successfully.
Feb 14 00:22:40 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Stopped caddy.service - Caddy.
Feb 14 00:22:40 vps.us-central1-f.c.munaimfinance.internal systemd[1]: caddy.service: Consumed 16.095s CPU time, 30.2M memory peak, 0B memory swap peak.
-- Boot 4b8128e076b34f9fbe84d70e074d25be --
Feb 14 00:23:03 vps systemd[1]: Starting caddy.service - Caddy...
Feb 14 00:23:05 vps caddy[671]: {"level":"info","ts":1771010585.0287309,"msg":"maxprocs: Leaving GOMAXPROCS=4: CPU quota undefined"}
Feb 14 00:23:05 vps caddy[671]: {"level":"info","ts":1771010585.0289917,"msg":"GOMEMLIMIT is updated","package":"github.com/KimMachineGun/automemlimit/memlimit","GOMEMLIMIT":20775459225,"previous":9223372036854775807}
Feb 14 00:23:05 vps caddy[671]: caddy.HomeDir=/var/lib/caddy
Feb 14 00:23:05 vps caddy[671]: caddy.AppDataDir=/var/lib/caddy/.local/share/caddy
Feb 14 00:23:05 vps caddy[671]: caddy.AppConfigDir=/var/lib/caddy/.config/caddy
Feb 14 00:23:05 vps caddy[671]: caddy.ConfigAutosavePath=/var/lib/caddy/.config/caddy/autosave.json
Feb 14 00:23:05 vps caddy[671]: caddy.Version=v2.10.2 h1:g/gTYjGMD0dec+UgMw8SnfmJ3I9+M2TdvoRL/Ovu6U8=
Feb 14 00:23:05 vps caddy[671]: runtime.GOOS=linux
Feb 14 00:23:05 vps caddy[671]: runtime.GOARCH=amd64
Feb 14 00:23:05 vps caddy[671]: runtime.Compiler=gc
Feb 14 00:23:05 vps caddy[671]: runtime.NumCPU=4
Feb 14 00:23:05 vps caddy[671]: runtime.GOMAXPROCS=4
Feb 14 00:23:05 vps caddy[671]: runtime.Version=go1.25.0
Feb 14 00:23:05 vps caddy[671]: os.Getwd=/
Feb 14 00:23:05 vps caddy[671]: LANG=C.UTF-8
Feb 14 00:23:05 vps caddy[671]: PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/snap/bin
Feb 14 00:23:05 vps caddy[671]: NOTIFY_SOCKET=/run/systemd/notify
Feb 14 00:23:05 vps caddy[671]: USER=caddy
Feb 14 00:23:05 vps caddy[671]: LOGNAME=caddy
Feb 14 00:23:05 vps caddy[671]: HOME=/var/lib/caddy
Feb 14 00:23:05 vps caddy[671]: INVOCATION_ID=a56db18a3f5642308235447a7a1619b9
Feb 14 00:23:05 vps caddy[671]: JOURNAL_STREAM=9:6612
Feb 14 00:23:05 vps caddy[671]: SYSTEMD_EXEC_PID=671
Feb 14 00:23:05 vps caddy[671]: MEMORY_PRESSURE_WATCH=/sys/fs/cgroup/system.slice/caddy.service/memory.pressure
Feb 14 00:23:05 vps caddy[671]: MEMORY_PRESSURE_WRITE=c29tZSAyMDAwMDAgMjAwMDAwMAA=
Feb 14 00:23:05 vps caddy[671]: {"level":"info","ts":1771010585.0308406,"msg":"using config from file","file":"/etc/caddy/Caddyfile"}
Feb 14 00:23:05 vps caddy[671]: {"level":"info","ts":1771010585.0519452,"msg":"adapted config to JSON","adapter":"caddyfile"}
Feb 14 00:23:05 vps caddy[671]: {"level":"warn","ts":1771010585.0519726,"msg":"Caddyfile input is not formatted; run 'caddy fmt --overwrite' to fix inconsistencies","adapter":"caddyfile","file":"/etc/caddy/Caddyfile","line":388}
Feb 14 00:23:05 vps caddy[671]: {"level":"info","ts":1771010585.0594468,"msg":"redirected default logger","from":"stderr","to":"/home/munaim/srv/proxy/caddy/logs/error.log"}
Feb 14 00:23:05 vps caddy[671]: {"level":"info","ts":1771010585.1217694,"msg":"serving initial configuration"}
Feb 14 00:23:17 vps systemd[1]: Started caddy.service - Caddy.
Feb 14 02:03:52 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Reloading caddy.service - Caddy...
Feb 14 02:03:52 vps.us-central1-f.c.munaimfinance.internal caddy[13695]: {"level":"info","ts":1771016632.6027403,"msg":"using config from file","file":"/etc/caddy/Caddyfile"}
Feb 14 02:03:52 vps.us-central1-f.c.munaimfinance.internal caddy[13695]: {"level":"info","ts":1771016632.6136758,"msg":"adapted config to JSON","adapter":"caddyfile"}
Feb 14 02:03:52 vps.us-central1-f.c.munaimfinance.internal caddy[13695]: {"level":"warn","ts":1771016632.613698,"msg":"Caddyfile input is not formatted; run 'caddy fmt --overwrite' to fix inconsistencies","adapter":"caddyfile","file":"/etc/caddy/Caddyfile","line":388}
Feb 14 02:03:52 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Reloaded caddy.service - Caddy.
Feb 14 02:12:23 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.7710171434781454e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_api.pgsims.pmc.edu.pk.lock)
Feb 14 02:19:05 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.7710175454494596e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_sims.pmc.edu.pk.lock)
Feb 14 02:19:05 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.7710175454876852e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_pgsims.pmc.edu.pk.lock)
Feb 14 02:19:05 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.7710175454876964e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_api.sos.alshifalab.pk.lock)
Feb 14 02:56:23 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Reloading caddy.service - Caddy...
Feb 14 02:56:23 vps.us-central1-f.c.munaimfinance.internal caddy[144473]: {"level":"info","ts":1771019783.1311245,"msg":"using config from file","file":"/etc/caddy/Caddyfile"}
Feb 14 02:56:23 vps.us-central1-f.c.munaimfinance.internal caddy[144473]: {"level":"info","ts":1771019783.1481872,"msg":"adapted config to JSON","adapter":"caddyfile"}
Feb 14 02:56:23 vps.us-central1-f.c.munaimfinance.internal caddy[144473]: {"level":"warn","ts":1771019783.1482108,"msg":"Caddyfile input is not formatted; run 'caddy fmt --overwrite' to fix inconsistencies","adapter":"caddyfile","file":"/etc/caddy/Caddyfile","line":461}
Feb 14 02:56:23 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Reloaded caddy.service - Caddy.
Feb 14 03:39:43 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.7710223831783936e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_api.sims.pmc.edu.pk.lock)
Feb 14 04:57:50 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.7710270708115144e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_api.sos.alshifalab.pk.lock)
Feb 14 04:58:05 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.7710270858256445e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_sims.pmc.edu.pk.lock)
Feb 14 04:58:05 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.7710270858269675e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_pgsims.pmc.edu.pk.lock)
Feb 14 04:58:50 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.771027130871959e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_api.pgsims.pmc.edu.pk.lock)
Feb 14 04:59:00 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.7710271408823588e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_api.sims.pmc.edu.pk.lock)
Feb 14 06:18:16 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Reloading caddy.service - Caddy...
Feb 14 06:18:17 vps.us-central1-f.c.munaimfinance.internal caddy[635551]: {"level":"info","ts":1771031897.0513554,"msg":"using config from file","file":"/etc/caddy/Caddyfile"}
Feb 14 06:18:17 vps.us-central1-f.c.munaimfinance.internal caddy[635551]: {"level":"info","ts":1771031897.0662773,"msg":"adapted config to JSON","adapter":"caddyfile"}
Feb 14 06:18:17 vps.us-central1-f.c.munaimfinance.internal caddy[635551]: {"level":"warn","ts":1771031897.0663068,"msg":"Caddyfile input is not formatted; run 'caddy fmt --overwrite' to fix inconsistencies","adapter":"caddyfile","file":"/etc/caddy/Caddyfile","line":461}
Feb 14 06:18:17 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Reloaded caddy.service - Caddy.
Feb 14 06:30:05 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Reloading caddy.service - Caddy...
Feb 14 06:30:05 vps.us-central1-f.c.munaimfinance.internal caddy[666842]: {"level":"info","ts":1771032605.4246445,"msg":"using config from file","file":"/etc/caddy/Caddyfile"}
Feb 14 06:30:05 vps.us-central1-f.c.munaimfinance.internal caddy[666842]: {"level":"info","ts":1771032605.438335,"msg":"adapted config to JSON","adapter":"caddyfile"}
Feb 14 06:30:05 vps.us-central1-f.c.munaimfinance.internal caddy[666842]: {"level":"warn","ts":1771032605.4383566,"msg":"Caddyfile input is not formatted; run 'caddy fmt --overwrite' to fix inconsistencies","adapter":"caddyfile","file":"/etc/caddy/Caddyfile","line":462}
Feb 14 06:30:05 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Reloaded caddy.service - Caddy.
Feb 14 06:39:08 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Reloading caddy.service - Caddy...
Feb 14 06:39:08 vps.us-central1-f.c.munaimfinance.internal caddy[689455]: {"level":"info","ts":1771033148.159293,"msg":"using config from file","file":"/etc/caddy/Caddyfile"}
Feb 14 06:39:08 vps.us-central1-f.c.munaimfinance.internal caddy[689455]: {"level":"info","ts":1771033148.17765,"msg":"adapted config to JSON","adapter":"caddyfile"}
Feb 14 06:39:08 vps.us-central1-f.c.munaimfinance.internal caddy[689455]: {"level":"warn","ts":1771033148.177673,"msg":"Caddyfile input is not formatted; run 'caddy fmt --overwrite' to fix inconsistencies","adapter":"caddyfile","file":"/etc/caddy/Caddyfile","line":459}
Feb 14 06:39:08 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Reloaded caddy.service - Caddy.
Feb 14 06:50:10 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Reloading caddy.service - Caddy...
Feb 14 06:50:10 vps.us-central1-f.c.munaimfinance.internal caddy[716603]: {"level":"info","ts":1771033810.6736639,"msg":"using config from file","file":"/etc/caddy/Caddyfile"}
Feb 14 06:50:10 vps.us-central1-f.c.munaimfinance.internal caddy[716603]: {"level":"info","ts":1771033810.687263,"msg":"adapted config to JSON","adapter":"caddyfile"}
Feb 14 06:50:10 vps.us-central1-f.c.munaimfinance.internal caddy[716603]: {"level":"warn","ts":1771033810.6872866,"msg":"Caddyfile input is not formatted; run 'caddy fmt --overwrite' to fix inconsistencies","adapter":"caddyfile","file":"/etc/caddy/Caddyfile","line":455}
Feb 14 06:50:10 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Reloaded caddy.service - Caddy.
Feb 14 08:42:55 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.7710405757198489e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_sims.pmc.edu.pk.lock)
Feb 14 08:49:05 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.7710409459692125e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_pgsims.pmc.edu.pk.lock)
Feb 14 08:49:30 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.7710409709857633e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_api.mediq.alshifalab.pk.lock)
Feb 14 08:49:45 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.771040985998182e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_api.sims.pmc.edu.pk.lock)
Feb 14 08:50:16 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.7710410160170655e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_api.pgsims.pmc.edu.pk.lock)
Feb 14 09:54:48 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.7710448888446314e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_api.sims.pmc.edu.pk.lock)
Feb 14 09:55:18 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.7710449188676836e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_api.sos.alshifalab.pk.lock)
Feb 14 10:03:29 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.7710454092860572e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_sims.pmc.edu.pk.lock)
Feb 14 10:03:34 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.771045414289574e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_api.sims.pmc.edu.pk.lock)
Feb 14 10:33:55 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.7710472359889145e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_sims.pmc.edu.pk.lock)
Feb 14 10:47:46 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.771048066764363e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_api.pgsims.pmc.edu.pk.lock)
Feb 14 10:47:56 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.7710480767719305e+09        error        Keeping lock file fresh: invalid character '}' after top-level value - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_pgsims.pmc.edu.pk.lock)
Feb 14 10:47:56 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.7710480767719285e+09        error        Keeping lock file fresh: invalid character '}' after top-level value - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_pgsims.pmc.edu.pk.lock)
Feb 14 10:49:16 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.7710481568253546e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_api.mediq.alshifalab.pk.lock)
Feb 14 10:49:56 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.7710481968584611e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_api.sos.alshifalab.pk.lock)
Feb 15 00:00:02 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Reloading caddy.service - Caddy...
Feb 15 00:00:02 vps.us-central1-f.c.munaimfinance.internal caddy[3210805]: {"level":"info","ts":1771095602.90768,"msg":"using config from file","file":"/etc/caddy/Caddyfile"}
Feb 15 00:00:02 vps.us-central1-f.c.munaimfinance.internal caddy[3210805]: {"level":"info","ts":1771095602.922967,"msg":"adapted config to JSON","adapter":"caddyfile"}
Feb 15 00:00:02 vps.us-central1-f.c.munaimfinance.internal caddy[3210805]: {"level":"warn","ts":1771095602.923,"msg":"Caddyfile input is not formatted; run 'caddy fmt --overwrite' to fix inconsistencies","adapter":"caddyfile","file":"/etc/caddy/Caddyfile","line":455}
Feb 15 00:00:02 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.7710956029420536e+09        info        [FileStorage:/var/lib/caddy/.local/share/caddy] Lock for 'issue_cert_pgsims.pmc.edu.pk' is stale (created: 2026-02-14 06:50:10.70596103 +0500 PKT, last update: 2026-02-14 10:47:51.7694055 +0500 PKT); removing then retrying: /var/lib/caddy/.local/share/caddy/locks/issue_cert_pgsims.pmc.edu.pk.lock
Feb 15 00:00:02 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Reloaded caddy.service - Caddy.
Feb 15 00:05:23 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.7710959231275597e+09        error        Keeping lock file fresh: invalid character '}' after top-level value - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_api.pgsims.pmc.edu.pk.lock)
Feb 15 00:05:23 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.7710959231275816e+09        error        Keeping lock file fresh: invalid character '}' after top-level value - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_api.pgsims.pmc.edu.pk.lock)
Feb 15 00:58:40 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.7710991209174325e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_api.mediq.alshifalab.pk.lock)
Feb 15 00:58:45 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.7710991259223475e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_sims.pmc.edu.pk.lock)
Feb 15 00:58:50 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.771099130926626e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_api.sims.pmc.edu.pk.lock)
Feb 15 00:59:05 vps.us-central1-f.c.munaimfinance.internal caddy[671]: 1.7710991459381804e+09        error        Keeping lock file fresh: unexpected end of JSON input - terminating lock maintenance (lockfile: /var/lib/caddy/.local/share/caddy/locks/issue_cert_api.sos.alshifalab.pk.lock)
Feb 15 04:34:55 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Stopping caddy.service - Caddy...
Feb 15 04:34:56 vps.us-central1-f.c.munaimfinance.internal systemd[1]: caddy.service: Deactivated successfully.
Feb 15 04:34:56 vps.us-central1-f.c.munaimfinance.internal systemd[1]: Stopped caddy.service - Caddy.
Feb 15 04:34:56 vps.us-central1-f.c.munaimfinance.internal systemd[1]: caddy.service: Consumed 1min 18.523s CPU time, 70.3M memory peak, 0B memory swap peak.
-- Boot 80c74a79ffcc420d9c355fcc951e6ca8 --
Feb 15 04:35:20 vps systemd[1]: Starting caddy.service - Caddy...
Feb 15 04:35:22 vps caddy[688]: {"level":"info","ts":1771112122.0126247,"msg":"maxprocs: Leaving GOMAXPROCS=4: CPU quota undefined"}
Feb 15 04:35:22 vps caddy[688]: {"level":"info","ts":1771112122.0134966,"msg":"GOMEMLIMIT is updated","package":"github.com/KimMachineGun/automemlimit/memlimit","GOMEMLIMIT":20775455539,"previous":9223372036854775807}
Feb 15 04:35:22 vps caddy[688]: caddy.HomeDir=/var/lib/caddy
Feb 15 04:35:22 vps caddy[688]: caddy.AppDataDir=/var/lib/caddy/.local/share/caddy
Feb 15 04:35:22 vps caddy[688]: caddy.AppConfigDir=/var/lib/caddy/.config/caddy
Feb 15 04:35:22 vps caddy[688]: caddy.ConfigAutosavePath=/var/lib/caddy/.config/caddy/autosave.json
Feb 15 04:35:22 vps caddy[688]: caddy.Version=v2.10.2 h1:g/gTYjGMD0dec+UgMw8SnfmJ3I9+M2TdvoRL/Ovu6U8=
Feb 15 04:35:22 vps caddy[688]: runtime.GOOS=linux
Feb 15 04:35:22 vps caddy[688]: runtime.GOARCH=amd64
Feb 15 04:35:22 vps caddy[688]: runtime.Compiler=gc
Feb 15 04:35:22 vps caddy[688]: runtime.NumCPU=4
Feb 15 04:35:22 vps caddy[688]: runtime.GOMAXPROCS=4
Feb 15 04:35:22 vps caddy[688]: runtime.Version=go1.25.0
Feb 15 04:35:22 vps caddy[688]: os.Getwd=/
Feb 15 04:35:22 vps caddy[688]: LANG=C.UTF-8
Feb 15 04:35:22 vps caddy[688]: PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/snap/bin
Feb 15 04:35:22 vps caddy[688]: NOTIFY_SOCKET=/run/systemd/notify
Feb 15 04:35:22 vps caddy[688]: USER=caddy
Feb 15 04:35:22 vps caddy[688]: LOGNAME=caddy
Feb 15 04:35:22 vps caddy[688]: HOME=/var/lib/caddy
Feb 15 04:35:22 vps caddy[688]: INVOCATION_ID=f12340ca26ca407ebce2f7a23148a9ea
Feb 15 04:35:22 vps caddy[688]: JOURNAL_STREAM=9:5726
Feb 15 04:35:22 vps caddy[688]: SYSTEMD_EXEC_PID=688
```


## Caddyfile diff (srv vs /etc) (top)

### Caddyfile diff

```

```


## Domain probes (top)

### domain probes (headers + short bodies)

```
## 127.0.0.1:13000/
https://127.0.0.1:13000/
curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

----

## 127.0.0.1:13000/health
https://127.0.0.1:13000/health
curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

----

## 127.0.0.1:13000/healthz
https://127.0.0.1:13000/healthz
curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

----

## 127.0.0.1:13000/api
https://127.0.0.1:13000/api
curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

----

## 127.0.0.1:13000/api/
https://127.0.0.1:13000/api/
curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

----

## 127.0.0.1:13000/api/v1
https://127.0.0.1:13000/api/v1
curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

----

## 127.0.0.1:13000/api/v1/
https://127.0.0.1:13000/api/v1/
curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

----

## 127.0.0.1:13000/api/auth
https://127.0.0.1:13000/api/auth
curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

----

## 127.0.0.1:13000/api/auth/
https://127.0.0.1:13000/api/auth/
curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

----

## 127.0.0.1:13000/auth
https://127.0.0.1:13000/auth
curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

----

## 127.0.0.1:13000/auth/
https://127.0.0.1:13000/auth/
curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

----

## 127.0.0.1:13000/admin
https://127.0.0.1:13000/admin
curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

----

## 127.0.0.1:13000/admin/
https://127.0.0.1:13000/admin/
curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

----

## 127.0.0.1:13000/api/schema
https://127.0.0.1:13000/api/schema
curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

----

## 127.0.0.1:13000/api/docs
https://127.0.0.1:13000/api/docs
curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

----

## 127.0.0.1:18000/
https://127.0.0.1:18000/
curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

----

## 127.0.0.1:18000/health
https://127.0.0.1:18000/health
curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

----

## 127.0.0.1:18000/healthz
https://127.0.0.1:18000/healthz
curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

----

## 127.0.0.1:18000/api
https://127.0.0.1:18000/api
curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

----

## 127.0.0.1:18000/api/
https://127.0.0.1:18000/api/
curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

----

## 127.0.0.1:18000/api/v1
https://127.0.0.1:18000/api/v1
curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

----

## 127.0.0.1:18000/api/v1/
https://127.0.0.1:18000/api/v1/
curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

----

## 127.0.0.1:18000/api/auth
https://127.0.0.1:18000/api/auth
curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

----

## 127.0.0.1:18000/api/auth/
https://127.0.0.1:18000/api/auth/
curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

----

## 127.0.0.1:18000/auth
https://127.0.0.1:18000/auth
curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

----

## 127.0.0.1:18000/auth/
https://127.0.0.1:18000/auth/
curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

----

## 127.0.0.1:18000/admin
https://127.0.0.1:18000/admin
curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

----

## 127.0.0.1:18000/admin/
https://127.0.0.1:18000/admin/
curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server
```


## Localhost upstream probes (top)

### localhost upstream probes

```
## http://127.0.0.1:13000/
curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

## http://127.0.0.1:13000/health
curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

## http://127.0.0.1:13000/healthz
curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

## http://127.0.0.1:13000/api/
curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

## http://127.0.0.1:13000/api/v1/
curl: (7) Failed to connect to 127.0.0.1 port 13000 after 0 ms: Couldn't connect to server

----

## http://127.0.0.1:18000/
curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

## http://127.0.0.1:18000/health
curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

## http://127.0.0.1:18000/healthz
curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

## http://127.0.0.1:18000/api/
curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

## http://127.0.0.1:18000/api/v1/
curl: (7) Failed to connect to 127.0.0.1 port 18000 after 0 ms: Couldn't connect to server

----

## http://127.0.0.1:18001/
curl: (7) Failed to connect to 127.0.0.1 port 18001 after 0 ms: Couldn't connect to server

## http://127.0.0.1:18001/health
curl: (7) Failed to connect to 127.0.0.1 port 18001 after 0 ms: Couldn't connect to server

## http://127.0.0.1:18001/healthz
curl: (7) Failed to connect to 127.0.0.1 port 18001 after 0 ms: Couldn't connect to server

## http://127.0.0.1:18001/api/
curl: (7) Failed to connect to 127.0.0.1 port 18001 after 0 ms: Couldn't connect to server

## http://127.0.0.1:18001/api/v1/
curl: (7) Failed to connect to 127.0.0.1 port 18001 after 0 ms: Couldn't connect to server

----

## http://127.0.0.1:3025/
curl: (7) Failed to connect to 127.0.0.1 port 3025 after 0 ms: Couldn't connect to server

## http://127.0.0.1:3025/health
curl: (7) Failed to connect to 127.0.0.1 port 3025 after 0 ms: Couldn't connect to server

## http://127.0.0.1:3025/healthz
curl: (7) Failed to connect to 127.0.0.1 port 3025 after 0 ms: Couldn't connect to server

## http://127.0.0.1:3025/api/
curl: (7) Failed to connect to 127.0.0.1 port 3025 after 0 ms: Couldn't connect to server

## http://127.0.0.1:3025/api/v1/
curl: (7) Failed to connect to 127.0.0.1 port 3025 after 0 ms: Couldn't connect to server

----

## http://127.0.0.1:8010/
curl: (7) Failed to connect to 127.0.0.1 port 8010 after 0 ms: Couldn't connect to server

## http://127.0.0.1:8010/health
curl: (7) Failed to connect to 127.0.0.1 port 8010 after 0 ms: Couldn't connect to server

## http://127.0.0.1:8010/healthz
curl: (7) Failed to connect to 127.0.0.1 port 8010 after 0 ms: Couldn't connect to server

## http://127.0.0.1:8010/api/
curl: (7) Failed to connect to 127.0.0.1 port 8010 after 0 ms: Couldn't connect to server

## http://127.0.0.1:8010/api/v1/
curl: (7) Failed to connect to 127.0.0.1 port 8010 after 0 ms: Couldn't connect to server

----

## http://127.0.0.1:8011/
curl: (7) Failed to connect to 127.0.0.1 port 8011 after 0 ms: Couldn't connect to server

## http://127.0.0.1:8011/health
curl: (7) Failed to connect to 127.0.0.1 port 8011 after 0 ms: Couldn't connect to server

## http://127.0.0.1:8011/healthz
curl: (7) Failed to connect to 127.0.0.1 port 8011 after 0 ms: Couldn't connect to server

## http://127.0.0.1:8011/api/
curl: (7) Failed to connect to 127.0.0.1 port 8011 after 0 ms: Couldn't connect to server

## http://127.0.0.1:8011/api/v1/
curl: (7) Failed to connect to 127.0.0.1 port 8011 after 0 ms: Couldn't connect to server

----

## http://127.0.0.1:8012/
HTTP/1.1 200 OK
Accept-Ranges: bytes
Content-Length: 460
Content-Type: text/html
Date: Sun, 15 Feb 2026 00:20:35 GMT
Etag: "69910846-1cc"
Last-Modified: Sat, 14 Feb 2026 23:41:58 GMT
Referrer-Policy: strict-origin-when-cross-origin
Server: nginx/1.29.5
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Via: 1.1 Caddy
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-Xss-Protection: 1; mode=block


## http://127.0.0.1:8012/health
HTTP/1.1 200 OK
Content-Type: text/plain; charset=utf-8
Referrer-Policy: strict-origin-when-cross-origin
Server: LIMS/1.0
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-Xss-Protection: 1; mode=block
Date: Sun, 15 Feb 2026 00:20:35 GMT
Content-Length: 2


## http://127.0.0.1:8012/healthz
HTTP/1.1 200 OK
Accept-Ranges: bytes
Content-Length: 460
Content-Type: text/html
Date: Sun, 15 Feb 2026 00:20:35 GMT
Etag: "69910846-1cc"
Last-Modified: Sat, 14 Feb 2026 23:41:58 GMT
Referrer-Policy: strict-origin-when-cross-origin
Server: nginx/1.29.5
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Via: 1.1 Caddy
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-Xss-Protection: 1; mode=block


## http://127.0.0.1:8012/api/
HTTP/1.1 404 Not Found
Content-Length: 4255
Content-Type: text/html; charset=utf-8
Cross-Origin-Opener-Policy: same-origin
Date: Sun, 15 Feb 2026 00:20:35 GMT
Referrer-Policy: strict-origin-when-cross-origin
Referrer-Policy: same-origin
Server: gunicorn
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Vary: origin, Cookie
Via: 1.1 Caddy
X-Content-Type-Options: nosniff
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-Frame-Options: DENY
X-Xss-Protection: 1; mode=block


## http://127.0.0.1:8012/api/v1/
HTTP/1.1 404 Not Found
Content-Length: 4264
Content-Type: text/html; charset=utf-8
Cross-Origin-Opener-Policy: same-origin
Date: Sun, 15 Feb 2026 00:20:35 GMT
Referrer-Policy: strict-origin-when-cross-origin
Referrer-Policy: same-origin
Server: gunicorn
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Vary: origin, Cookie
Via: 1.1 Caddy
X-Content-Type-Options: nosniff
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-Frame-Options: DENY
X-Xss-Protection: 1; mode=block


----

## http://127.0.0.1:8014/
curl: (7) Failed to connect to 127.0.0.1 port 8014 after 0 ms: Couldn't connect to server

## http://127.0.0.1:8014/health
curl: (7) Failed to connect to 127.0.0.1 port 8014 after 0 ms: Couldn't connect to server

## http://127.0.0.1:8014/healthz
curl: (7) Failed to connect to 127.0.0.1 port 8014 after 0 ms: Couldn't connect to server

## http://127.0.0.1:8014/api/
curl: (7) Failed to connect to 127.0.0.1 port 8014 after 0 ms: Couldn't connect to server

## http://127.0.0.1:8014/api/v1/
curl: (7) Failed to connect to 127.0.0.1 port 8014 after 0 ms: Couldn't connect to server

----

## http://127.0.0.1:8015/
curl: (7) Failed to connect to 127.0.0.1 port 8015 after 0 ms: Couldn't connect to server

## http://127.0.0.1:8015/health
curl: (7) Failed to connect to 127.0.0.1 port 8015 after 0 ms: Couldn't connect to server

## http://127.0.0.1:8015/healthz
curl: (7) Failed to connect to 127.0.0.1 port 8015 after 0 ms: Couldn't connect to server

## http://127.0.0.1:8015/api/
curl: (7) Failed to connect to 127.0.0.1 port 8015 after 0 ms: Couldn't connect to server

## http://127.0.0.1:8015/api/v1/
curl: (7) Failed to connect to 127.0.0.1 port 8015 after 0 ms: Couldn't connect to server
```


## Networking snapshot (top)

### listening ports + ufw

```
### Listening TCP
State  Recv-Q Send-Q Local Address:Port Peer Address:PortProcess                                                                                                                                        
LISTEN 0      4096       127.0.0.1:2019      0.0.0.0:*                                                                                                                                                  
LISTEN 0      2048       127.0.0.1:8000      0.0.0.0:*    users:(("gunicorn",pid=1163,fd=5),("gunicorn",pid=1162,fd=5),("gunicorn",pid=1160,fd=5),("gunicorn",pid=1152,fd=5),("gunicorn",pid=1102,fd=5))
LISTEN 0      4096       127.0.0.1:8012      0.0.0.0:*                                                                                                                                                  
LISTEN 0      4096       127.0.0.1:8013      0.0.0.0:*                                                                                                                                                  
LISTEN 0      200        127.0.0.1:5432      0.0.0.0:*                                                                                                                                                  
LISTEN 0      4096         0.0.0.0:22        0.0.0.0:*                                                                                                                                                  
LISTEN 0      4096   127.0.0.53%lo:53        0.0.0.0:*                                                                                                                                                  
LISTEN 0      4096      127.0.0.54:53        0.0.0.0:*                                                                                                                                                  
LISTEN 0      4096               *:80              *:*                                                                                                                                                  
LISTEN 0      4096            [::]:22           [::]:*                                                                                                                                                  
LISTEN 0      4096               *:443             *:*                                                                                                                                                  

### Listening UDP
State  Recv-Q Send-Q   Local Address:Port Peer Address:PortProcess
UNCONN 0      0           127.0.0.54:53        0.0.0.0:*          
UNCONN 0      0        127.0.0.53%lo:53        0.0.0.0:*          
UNCONN 0      0      10.128.0.2%ens4:68        0.0.0.0:*          
UNCONN 0      0            127.0.0.1:323       0.0.0.0:*          
UNCONN 0      0                [::1]:323          [::]:*          
UNCONN 0      0                    *:443             *:*          

### UFW
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), deny (routed)
New profiles: skip

To                         Action      From
--                         ------      ----
22/tcp (OpenSSH)           ALLOW IN    Anywhere                  
80                         ALLOW IN    Anywhere                  
443                        ALLOW IN    Anywhere                  
22/tcp (OpenSSH (v6))      ALLOW IN    Anywhere (v6)             
80 (v6)                    ALLOW IN    Anywhere (v6)             
443 (v6)                   ALLOW IN    Anywhere (v6)             
```


## Compose files discovered

```
/home/munaim/srv/apps/accredivault/infra/docker-compose.prod.yml
/home/munaim/srv/apps/accredivault/infra/docker-compose.yml
/home/munaim/srv/apps/consult/docker-compose.coolify.yml
/home/munaim/srv/apps/consult/docker-compose.dev.yml
/home/munaim/srv/apps/consult/docker-compose.prod.yml
/home/munaim/srv/apps/consult/docker-compose.yml
/home/munaim/srv/apps/consult/templates/docker-compose-app-template.yml
/home/munaim/srv/apps/dashboard/docker-compose.yml
/home/munaim/srv/apps/fmu-platform/docker-compose.dev.yml
/home/munaim/srv/apps/fmu-platform/docker-compose.prod.yml
/home/munaim/srv/apps/fmu-platform/docker-compose.yml
/home/munaim/srv/apps/lims/docker-compose.dev.yml
/home/munaim/srv/apps/lims/docker-compose.override.yml
/home/munaim/srv/apps/lims/docker-compose.prod.yml
/home/munaim/srv/apps/lims/docker-compose.yml
/home/munaim/srv/apps/pgsims/docker-compose.coolify.yml
/home/munaim/srv/apps/pgsims/docker-compose.dev.yml
/home/munaim/srv/apps/pgsims/docker-compose.local.yml
/home/munaim/srv/apps/pgsims/docker-compose.phc.yml
/home/munaim/srv/apps/pgsims/docker-compose.prod.yml
/home/munaim/srv/apps/pgsims/docker-compose.yml
/home/munaim/srv/apps/radreport/backend/docker-compose.yml
/home/munaim/srv/apps/radreport/docker-compose.dev.yml
/home/munaim/srv/apps/radreport/docker-compose.prod.yml
/home/munaim/srv/apps/radreport/docker-compose.yml
/home/munaim/srv/dashboard/docker-compose.yml
/home/munaim/srv/observability/docker-compose.yml
```

## Where to look next (actionable triage list)

1) If **domain probes show 200 for /** but API paths 404 → fix frontend API base + standardize API prefix.
2) If **domain probes show 502/504** → upstream not reachable; check container binding + port map.
3) If **CORS preflight missing Access-Control-Allow-Origin** → fix Caddy headers or app CORS allowlist.
4) If **Caddyfile diff is non-empty** → /etc/caddy may not match srv truth; sync drift exists.
5) If **localhost probes pass but domain probes fail** → Caddy routing rule mismatch.

