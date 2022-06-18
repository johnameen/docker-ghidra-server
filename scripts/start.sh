VERSION="10.1.2"
GHIDRA_USERS="admin"
LOCAL_ONLY=""
# INTERFACE_NAME=$(ip link | awk -F: '$0 !~ "lo|vir|wl|^[^0-9]"{print $2;getline}')
# INTERFACE_NAME=eno2
# IP_ADDRESS=$(ip -o -4 addr list ${INTERFACE_NAME} | awk '{print $4}' | cut -d/ -f1)

usage() { echo "Usage: $0 [-u <string of users>] -l start server as local only" 1>&2; exit 1; }

# if [ -f ".ghidra_users" ]; then
#   GHIDRA_USERS=$(head -n 1 filename)
# fi

while getopts ":lu::" o; do
   case "${o}" in
      u)
         GHIDRA_USERS=${OPTARG};;
      l)
         LOCAL_ONLY='-e GHIDRA_PUBLIC_HOSTNAME='${IP_ADDRESS};;
      *)
         usage;;
   esac
done

docker image inspect --format="Found ghidra_server container" "ghidra_server:${VERSION}" 2>/dev/null

if [ $? -ne 0 ]; then
    echo -e "\nGhidra_server image not build. Building..."
    docker build -t "ghidra_server:${VERSION}" .
    docker tag ghidra_server:${VERSION} ghidra_server:latest
fi

if [ -z "${GHIDRA_USERS}" ]; then
   echo "Error: user string was empty. Wrap arg in quotation marks"
   usage
fi

docker run -it --rm \
    --name ghidra-server \
    -e GHIDRA_USERS="${GHIDRA_USERS}" ${LOCAL_ONLY}\
    -v /home/john/silverado/ghidra_projects/:/repos \
    -p 13100-13102:13100-13102 \
    --net=host \
    ghidra_server:latest
