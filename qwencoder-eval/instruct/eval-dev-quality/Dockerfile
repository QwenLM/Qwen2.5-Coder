# Builder image.
FROM golang:latest AS builder

WORKDIR /app
COPY ./ ./

# Build the binary.
RUN go mod tidy
RUN CGO_ENABLED=0 go build -o eval-dev-quality ./cmd/eval-dev-quality

# Actual running image.
FROM ubuntu:noble
RUN apt-get update && \
	apt-get install -y \
	ca-certificates \
	gcc \
	git \
	libssl-dev \
	libtool \
	libyaml-dev \
	make \
	unzip \
	wget \
	zlib1g-dev \
	&& update-ca-certificates

# Switch to the ubuntu user as we want it to run as non-root.
USER ubuntu
WORKDIR /app
COPY --chown=ubuntu:ubuntu ./testdata ./testdata
COPY --chown=ubuntu:ubuntu ./Makefile ./Makefile
RUN mkdir -p .eval-dev-quality
RUN mkdir -p /app/evaluation

# Install Ruby
RUN mkdir -p /tmp/compile
RUN wget https://cache.ruby-lang.org/pub/ruby/3.3/ruby-3.3.4.tar.gz && \
	tar -xf ruby-3.3.4.tar.gz -C /tmp/compile/ && \
	rm ruby-3.3.4.tar.gz
WORKDIR /tmp/compile/ruby-3.3.4
RUN ./configure --prefix /app/.eval-dev-quality/ruby-3.3.4 --disable-install-doc
RUN	make install
WORKDIR /app
RUN rm -rf /tmp/compile
ENV PATH="${PATH}:/app/.eval-dev-quality/ruby-3.3.4/bin"

# Install Maven
RUN wget https://archive.apache.org/dist/maven/maven-3/3.9.1/binaries/apache-maven-3.9.1-bin.tar.gz && \
	tar -xf apache-maven-3.9.1-bin.tar.gz -C /app/.eval-dev-quality/ && \
	rm apache-maven-3.9.1-bin.tar.gz
ENV PATH="${PATH}:/app/.eval-dev-quality/apache-maven-3.9.1/bin"

# Install Gradle
RUN wget https://services.gradle.org/distributions/gradle-8.0.2-bin.zip && \
	unzip gradle-8.0.2-bin.zip -d /app/.eval-dev-quality/ && \
	rm gradle-8.0.2-bin.zip
ENV PATH="${PATH}:/app/.eval-dev-quality/gradle-8.0.2/bin"

# Install Java
RUN wget https://corretto.aws/downloads/resources/11.0.24.8.1/amazon-corretto-11.0.24.8.1-linux-x64.tar.gz && \
	tar -xf amazon-corretto-11.0.24.8.1-linux-x64.tar.gz -C /app/.eval-dev-quality/ && \
	rm amazon-corretto-11.0.24.8.1-linux-x64.tar.gz
ENV JAVA_HOME="/app/.eval-dev-quality/amazon-corretto-11.0.24.8.1-linux-x64"
ENV PATH="${PATH}:${JAVA_HOME}/bin"

# Install Go
RUN wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz && \
	tar -xf go1.21.5.linux-amd64.tar.gz -C /app/.eval-dev-quality/ && \
	rm go1.21.5.linux-amd64.tar.gz
ENV PATH="${PATH}:/app/.eval-dev-quality/go/bin"
ENV GOROOT="/app/.eval-dev-quality/go"
ENV PATH="${PATH}:/home/ubuntu/go/bin"

# Install the binary
COPY --from=builder --chown=ubuntu:ubuntu /app/eval-dev-quality /app/.eval-dev-quality/bin/
ENV PATH="${PATH}:/app/.eval-dev-quality/bin"
RUN make install-tools-testing
RUN make install-tools /app/.eval-dev-quality/bin
