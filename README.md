# Ghidra Docker Server

## Why?

Standing up a Ghidra Server in the cloud is a pain. It doesn't have to be. If you're new to Ghidra Server, [this primer](https://byte.how/posts/collaborative-reverse-engineering/) is a good introduction.

## Images

```bash
ghidra-server   latest
ghidra-server   10.1.1
```

> **NOTE:** tag `beta` is built by compiling Ghidra from its `master` branch source

## Getting Started

Start the server and connect to port 13100 with a Ghidra client that has a **matching** version. All users will be created as admins and will have initial password `changeme`, which Ghidra will require you to change after you login.

### Quick run

The start script will build the container if it's not already built.

```bash
./start.sh -h

./start.sh -u "admin bytehow" # Starts server with users "admin" and "noop"
./start.sh -l # Starts server as Local-only
```


### Public Server

```bash
$ docker run -it --rm \
    --name ghidra-server \
    -e GHIDRA_USERS="admin bytehow" \
    -v /path/to/repos:/repos \
    -p 13100-13102:13100-13102 \
    bytehow/ghidra-server
```

### Local-only Server

```bash
$ docker run -it --rm \
    --name ghidra-server \
    -e GHIDRA_USERS="admin bytehow" \
    -e GHIDRA_PUBLIC_HOSTNAME="0.0.0.0" \
    -v /path/to/repos:/repos \
    -p 13100-13102:13100-13102 \
    bytehow/ghidra-server
```


## Environment Variables

| Name | Description | Required | Default |
| - | - | - | - |
|`GHIDRA_USERS` | Space seperated list of users to create | No | `admin` |
|`GHIDRA_PUBLIC_HOSTNAME` | IP or hostname that remote users will use to connect to server. Set to `0.0.0.0` if hosting locally. If not set, it will try to discover your public ip by querying OpenDNS | No | Your public IP | 

## Additional information

Additional information such as capacity planning and other server configuration aspects can be found by consulting the server documentation provided at `/<GhidraInstallDir>/server/svrREADME.html`


## Issues

Find a bug? Want more features? Find something missing in the documentation? Let me know! Please don't hesitate to [file an issue](https://github.com/johnameen/docker-ghidra-server/issues/new)

## Credits

- NSA Research Directorate [https://www.ghidra-sre.org/](https://www.ghidra-sre.org/)
- blacktop's [docker-ghidra](https://github.com/blacktop/ghidra-server) project

### License

Apache License (Version 2.0)
