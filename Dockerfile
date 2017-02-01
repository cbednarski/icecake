FROM debian:latest
MAINTAINER Casey Strouse <casey.strouse@gmail.com>

RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  ca-certificates \
  curl \
  git \
  libbz2-dev \
  libssl-dev \
  libreadline-dev \
  libsqlite3-dev \
  pandoc \
  tcl-dev \
  xz-utils \
  zlib1g-dev \
&& rm -rf /var/lib/apt/lists/*

RUN git clone git://github.com/yyuu/pyenv.git .pyenv
ENV PYENV_ROOT $HOME/.pyenv
RUN git clone git://github.com/yyuu/pyenv-virtualenv.git $PYENV_ROOT/plugins/pyenv-virtualenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

RUN pyenv install 2.7.13 && \
    pyenv install 3.5.2

RUN pyenv global 2.7.13 && \
    pyenv local 2.7.13 3.5.2 && \
    pyenv rehash

RUN pip install -r requirements.txt

COPY . /icecake
WORKDIR /icecake

ENTRYPOINT ["make"]
CMD ["build"]
