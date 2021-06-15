from kafka import KafkaClient

client = KafkaClient(
    bootstrap_servers=[
        "b-1.shore-capital-kafka-cl.992ne4.c8.kafka.us-west-2.amazonaws.com:9092",
        "b-2.shore-capital-kafka-cl.992ne4.c8.kafka.us-west-2.amazonaws.com:9092",
    ]
)

client
