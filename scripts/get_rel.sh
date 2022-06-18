#!/bin/bash

repo=NationalSecurityAgency/ghidra

tag=$(curl -s "https://api.github.com/repos/$repo/releases/latest" > test.json)
exit
read type tag_sha < <(echo $(curl -s "https://api.github.com/repos/$repo/git/ref/tags/$tag" | 
     jq -r '.object.type,.object.sha'))

if [ $type == "commit" ]; then
    echo "commit sha: $tag_sha"
else
    sha=$(curl -s "https://api.github.com/repos/$repo/git/tags/$tag_sha" | jq '.object.sha')
    echo "commit sha: $sha"
fi
