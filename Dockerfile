FROM dockerregistry.test.netflix.net:7002/baseos/jammy:release

COPY ./ /project-snapshot

RUN apt-get update && \
    apt-get install -y git nflx-python-3.11 && \
    apt-get install -y nflx-ezconfig nflx-shrimpi proxyd gandalf-agent && \
    /apps/python3.11/bin/python -mvenv /apps/giphy-mcp-server && \
    /apps/giphy-mcp-server/bin/pip install -U pip --index-url https://pypi.netflix.net/simple && \
    /apps/giphy-mcp-server/bin/pip install --index-url https://pypi.netflix.net/simple /project-snapshot && \
    chown -R $NETFLIX_APPUSER /apps/giphy-mcp-server && \
    if [[ -d /project-snapshot/root ]]; then rsync -arHK /project-snapshot/root/ /; fi && \
    rm -rf /var/lib/apt/lists/* /project-snapshot

EXPOSE 7001
EXPOSE 7004
EXPOSE 443

CMD ["/nflx/bin/init"]
