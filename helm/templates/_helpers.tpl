{{/*
Expand the name of the chart.
*/}}
{{- define "ngt-archive.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "ngt-archive.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "ngt-archive.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "ngt-archive.labels" -}}
helm.sh/chart: {{ include "ngt-archive.chart" . }}
{{ include "ngt-archive.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "ngt-archive.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ngt-archive.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "ngt-archive.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "ngt-archive.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{/*
Rancher 2 annotations for annotations
*/}}
{{- define "ngt-archive.annotations" -}}
field.cattle.io/creatorId: {{ required "Please set .Values.k8.creatorId" .Values.k8.creatorId }}
{{- end }}


{{/*
Rancher 2 Ingress annotations
*/}}
{{- define "ngt-archive.annotations.ingress" -}}
nersc.gov/clustername: {{ required "Please set .Values.k8.clustername" .Values.k8.clustername }}
nersc.gov/serveralias: svc
nginx.ingress.kubernetes.io/enable-real-ip: "true"
nginx.ingress.kubernetes.io/proxy-real-ip-cidr: 10.42.0.0/16
nginx.ingress.kubernetes.io/use-forwarded-headers: "true"
nginx.ingress.kubernetes.io/proxy-body-size: "2096m"
{{- end }}

{{/*
The application version - allows it to be overridden by the image tag
*/}}
{{- define "ngt-archive.version" -}}
{{ default .Chart.AppVersion .Values.image.tag }}
{{- end }}


{{/*
Postgres Dump template definition
*/}}
{{- define "ngt-archive.pgdump-template" -}}
containers:
- name: pgdump
  env:
    - name: POSTGRES_DB
      value: ngeet
    - name: POSTGRES_DUMP_DIR
      value: /pg_dump
    - name: POSTGRES_DUMP_FILE_BASE
      value: ngeet-archive.sql.gz
    - name: POSTGRES_DUMP_RETAIN_DAYS
      value: "7"
    - name: POSTGRES_HOST
      value: db
    - name: POSTGRES_PASSWORD_FILE
      value: /secrets/db/db-password
    - name: POSTGRES_USER
      value: ngeet
    - name: TZ
      value: US/Pacific
  image: registry.nersc.gov/library/spin/postgres-pg_dump:12-alpine
  imagePullPolicy: Always
  resources: {}
  securityContext:
    allowPrivilegeEscalation: false
    capabilities:
      drop:
      - ALL
    privileged: false
    readOnlyRootFilesystem: false
    runAsNonRoot: false
    runAsUser: {{ .Values.uid }}
  stdin: true
  terminationMessagePath: /dev/termination-log
  terminationMessagePolicy: File
  tty: true
  volumeMounts:
  - mountPath: /pg_dump
    name: vol1
  - mountPath: /secrets/db
    name: vol2
    readOnly: true
dnsPolicy: ClusterFirst
{{- with .Values.imagePullSecrets }}
imagePullSecrets:
{{- toYaml . | nindent 2 }}
{{- end }}
restartPolicy: Never
securityContext:
  fsGroup: {{ .Values.gid }}
terminationGracePeriodSeconds: 30
volumes:
- hostPath:
    path: {{ tpl .Values.volume.backupDirectory . }}
    type: Directory
  name: vol1
- name: vol2
  secret:
    defaultMode: 256
    optional: false
    secretName: {{ .Values.secretName.database }}
{{- end}}