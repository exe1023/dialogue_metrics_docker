curl --header "Content-Type: application/json" \
  --request POST \
  -d @$1 \
  http://localhost:$2/
