from neo4j.time import Date, DateTime

def convert_neo4j_value(value):
    if isinstance(value, Date):
        return value.to_native()

    if isinstance(value, DateTime):
        return value.to_native()

    if isinstance(value, list):
        return [convert_neo4j_value(v) for v in value]

    if isinstance(value, dict):
        return {k: convert_neo4j_value(v) for k, v in value.items()}

    return value