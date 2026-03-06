VIDEO_MODEL_CONFIGS: dict[str, dict] = {
    "openai/sora-2/text-to-video": {
        "provider": "openai",
        "durations_seconds": [4, 8, 12],
        "sizes": ["720*1280", "1280*720"],
        "prices_usd_by_duration": {
            "4": {
                "720*1280": 0.40,
                "1280*720": 0.40,
            },
            "8": {
                "720*1280": 0.80,
                "1280*720": 0.80,
            },
            "12": {
                "720*1280": 1.20,
                "1280*720": 1.20,
            },
        },
    },
    "google/veo3.1/text-to-video": {
        "provider": "google",
        "durations_seconds": [4, 6, 8],
        "sizes": ["16:9", "9:16"],
        "prices_usd_by_duration": {
            "4": {
                "16:9": 1.60,
                "9:16": 1.60,
            },
            "6": {
                "16:9": 2.40,
                "9:16": 2.40,
            },
            "8": {
                "16:9": 3.20,
                "9:16": 3.20,
            },
        },
    },
}
