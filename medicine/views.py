
medicine_status = [
    {
        "name": "requiere_review",
        "public_name": "Requiere revisión",
        "order": 101,
        "color": "red",
    },
    {
        "name": "could_be_reviewed",
        "public_name": "Podría ser revisado",
        "order": 102,
        "color": "orange",
    },
    {
        "name": "only_one",
        "public_name": "Solo una opción",
        "order": 103,
        "color": "lime",
    },
    {
        "name": "almost_verified",
        "public_name": "Casi verificado",
        "order": 104,
        "color": "light-green",
    },
    {
        "name": "verified",
        "public_name": "Verificado",
        "order": 105,
        "color": "green",
    },
]

# Equivalencias de íconos a status_final:
equivalences = [
    {"summary_icons": "⭕", "status_final_id":  "requiere_review"},
    {"summary_icons": "3️⃣❌", "status_final_id": "requiere_review"},
    {"summary_icons": "⚠️2️⃣❌", "status_final_id":  "requiere_review"},
    {"summary_icons": "2️⃣❌", "status_final_id": "requiere_review"},
    {"summary_icons": "3️⃣✴️", "status_final_id": "could_be_reviewed"},
    {"summary_icons": "2️⃣✴️", "status_final_id": "could_be_reviewed"},
    {"summary_icons": "1️⃣️✴️", "status_final_id": "only_one"},
    {"summary_icons": "3️⃣❇️", "status_final_id": "almost_verified"},
    {"summary_icons": "3️⃣✅", "status_final_id": "verified"},
    {"summary_icons": "2️⃣❇️", "status_final_id": "verified"},
]
example_source_data = {
    "name": {
        "saved_data": "Ampicilina",
        "pdf": "Ampicilina",
        "web": "Ampicilina",
        "final": "Ampicilina",
        "original": "Ampicilina",
        "summary_icons": "3️⃣✅",
        "detail_icons": "✅|✅|✅",
    },
    "key": {
        "saved_data": "020.001.1",
        "pdf": "020.001.1",
        "web": "020.001.1",
        "final": "020.001.1",
        "original": "020.001.1",
        "summary_icons": "3️⃣✅",
        "detail_icons": "✅|✅|✅",
    }
}

