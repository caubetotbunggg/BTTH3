set -e

COLLECTION_DIR="postman"
REPORT_DIR="newman_reports"

mkdir -p $REPORT_DIR

echo "Running Newman tests for all collections in $COLLECTION_DIR ..."

for collection in $COLLECTION_DIR/*.json; do
    name=$(basename "$collection" .json)
    report_file="$REPORT_DIR/${name}_report.html"

    echo " Running collection: $collection"
    npx newman run "$collection" \
        --reporters cli,html \
        --reporter-html-export "$report_file"
done

echo " All Newman tests completed. Reports saved in $REPORT_DIR/"
