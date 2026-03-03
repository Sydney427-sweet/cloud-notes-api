from flask import Flask, request, jsonify
import uuid
import boto3
from botocore.exceptions import ClientError

app = Flask(__name__)

# --- DynamoDB Configuration ---
REGION = "us-east-1"           # replace with your table's region
TABLE_NAME = "Notes"           # exact table name

dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

# --- Ensure table exists ---
try:
    table.load()  # check if table exists
except ClientError as e:
    if e.response['Error']['Code'] == 'ResourceNotFoundException':
        # Table doesn't exist, create it
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        # Wait until the table exists
        table.meta.client.get_waiter('table_exists').wait(TableName=TABLE_NAME)
    else:
        raise e

# --- Routes ---

# Create a new note
@app.route("/notes", methods=["POST"])
def create_note():
    try:
        data = request.get_json()
        if not data or "content" not in data:
            return jsonify({"error": "Missing 'content' in request"}), 400

        note_id = str(uuid.uuid4())
        table.put_item(Item={"id": note_id, "content": data["content"]})
        return jsonify({"id": note_id, "content": data["content"]}), 201
    except ClientError as e:
        return jsonify({"error": str(e)}), 500

# Get all notes
@app.route("/notes", methods=["GET"])
def get_notes():
    try:
        response = table.scan()
        return jsonify(response.get("Items", [])), 200
    except ClientError as e:
        return jsonify({"error": str(e)}), 500

# Delete a note by ID
@app.route("/notes/<note_id>", methods=["DELETE"])
def delete_note(note_id):
    try:
        table.delete_item(Key={"id": note_id})
        return jsonify({"message": "Deleted"}), 200
    except ClientError as e:
        return jsonify({"error": str(e)}), 500

# --- Run Flask App ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
