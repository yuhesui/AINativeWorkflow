FROM registry.codeocean.com/codeocean/r-base:3.4.2-ubuntu16.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      "default-jdk=2:1.8-56ubuntu2" \
    && rm -rf /var/lib/apt/lists/*

RUN Rscript -e 'devtools::install_version("Hmisc", \
      version = "4.0-3", \
      dependencies = TRUE)'
RUN Rscript -e 'devtools::install_version("PRROC", \
      version = "1.3", \
      dependencies = TRUE)'
RUN Rscript -e 'devtools::install_version("PharmacoGx", \
      version = "1.1.6", \
      dependencies = TRUE)'
RUN Rscript -e 'devtools::install_version("ROCR", \
      version = "1.0-7", \
      dependencies = TRUE)'
RUN Rscript -e 'devtools::install_version("SNFtool", \
      version = "2.2.1", \
      dependencies = TRUE)'
RUN Rscript -e 'devtools::install_version("apcluster", \
      version = "1.4.4", \
      dependencies = TRUE)'
RUN Rscript -e 'devtools::install_version("fingerprint", \
      version = "3.5.6", \
      dependencies = TRUE)'
RUN Rscript -e 'devtools::install_version("proxy", \
      version = "0.4-20", \
      dependencies = TRUE)'
RUN Rscript -e 'devtools::install_version("rcdk", \
      version = "3.4.5", \
      dependencies = TRUE)'
RUN Rscript -e 'devtools::install_version("reshape2", \
      version = "1.4.2", \
      dependencies = TRUE)'

RUN Rscript -e ' \
      source("http://bioconductor.org/biocLite.R"); \
      biocLite(c( \
        "annotate", \
        "netbiov", \
        "org.Hs.eg.db", \
        "survcomp" \
      ), suppressUpdates = TRUE)'
