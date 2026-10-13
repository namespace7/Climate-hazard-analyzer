from config.database import analysis_collection

analysis_collection.create_index(
    [
        ("latitude", 1),
        ("longitude", 1),
        ("start_date", 1),
        ("end_date", 1),
    ],
    unique = True,
    name="unique_analysis_query",
)

print("Analysis index created successfully")