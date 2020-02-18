SRC_DIR=./protos
DST_DIR=./robots/proto/
protoc -I=$SRC_DIR --python_out=$DST_DIR $SRC_DIR/round.proto