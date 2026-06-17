"""Centralized API endpoint definitions for Garmin Connect."""


class Endpoints:
    """All API endpoint paths used by Garmin Connect integration.

    These are relative paths that are joined with the base connectapi URL.
    """

    # User & Profile
    USER_SETTINGS = "/userprofile-service/userprofile/user-settings"
    USERPROFILE_SETTINGS = "/userprofile-service/userprofile/settings"
    SOCIAL_PROFILE = "/userprofile-service/socialProfile"

    # Devices
    DEVICES = "/device-service/deviceregistration/devices"
    DEVICE = "/device-service/deviceservice"
    PRIMARY_DEVICE = "/web-gateway/device-info/primary-training-device"

    # Daily Summary & Metrics
    DAILY_SUMMARY = "/usersummary-service/usersummary/daily"
    DAILY_STEPS = "/usersummary-service/stats/steps/daily"
    WEEKLY_STEPS = "/usersummary-service/stats/steps/weekly"
    WEEKLY_STRESS = "/usersummary-service/stats/stress/weekly"
    WEEKLY_INTENSITY_MINUTES = "/usersummary-service/stats/im/weekly"
    MAX_METRICS = "/metrics-service/metrics/maxmet/daily"
    HILL_SCORE = "/metrics-service/metrics/hillscore"
    ENDURANCE_SCORE = "/metrics-service/metrics/endurancescore"
    TRAINING_READINESS = "/metrics-service/metrics/trainingreadiness"
    RACE_PREDICTOR = "/metrics-service/metrics/racepredictions"
    TRAINING_STATUS = "/metrics-service/metrics/trainingstatus/aggregated"
    RUNNING_TOLERANCE = "/metrics-service/metrics/runningtolerance/stats"

    # Health & Wellness
    DAILY_SLEEP = "/wellness-service/wellness/dailySleepData"
    DAILY_STRESS = "/wellness-service/wellness/dailyStress"
    DAILY_BODY_BATTERY = "/wellness-service/wellness/bodyBattery/reports/daily"
    BODY_BATTERY_EVENTS = "/wellness-service/wellness/bodyBattery/events"
    DAILY_RESPIRATION = "/wellness-service/wellness/daily/respiration"
    DAILY_SPO2 = "/wellness-service/wellness/daily/spo2"
    DAILY_INTENSITY_MINUTES = "/wellness-service/wellness/daily/im"
    DAILY_EVENTS = "/wellness-service/wellness/dailyEvents"
    USER_SUMMARY_CHART = "/wellness-service/wellness/dailySummaryChart"
    FLOORS_CHART_DAILY = "/wellness-service/wellness/floorsChartData/daily"
    HEARTRATES_DAILY = "/wellness-service/wellness/dailyHeartRate"
    DAILY_HYDRATION = "/usersummary-service/usersummary/hydration/daily"
    SET_HYDRATION = "/usersummary-service/usersummary/hydration/log"

    # Body Metrics
    WEIGHT = "/weight-service"
    BIOMETRIC = "/biometric-service/biometric"
    BIOMETRIC_STATS = "/biometric-service/stats"
    BLOOD_PRESSURE = "/bloodpressure-service/bloodpressure/range"
    SET_BLOOD_PRESSURE = "/bloodpressure-service/bloodpressure"

    # Health Conditions
    MENSTRUAL_CALENDAR = "/periodichealth-service/menstrualcycle/calendar"
    MENSTRUAL_DAYVIEW = "/periodichealth-service/menstrualcycle/dayview"
    PREGNANCY_SNAPSHOT = "/periodichealth-service/menstrualcycle/pregnancysnapshot"

    # Biometrics
    RHR = "/userstats-service/wellness/daily"
    HRV = "/hrv-service/hrv"
    FITNESSAGE = "/fitnessage-service/fitnessage"

    # Activities
    ACTIVITIES = "/activitylist-service/activities/search/activities"
    ACTIVITIES_COUNT = "/activitylist-service/activities/count"
    ACTIVITIES_BASEURL = "/activitylist-service/activities/"
    ACTIVITY = "/activity-service/activity"
    ACTIVITY_TYPES = "/activity-service/activity/activityTypes"
    ACTIVITY_FORDATE = "/mobile-gateway/heartRate/forDate"
    FITNESSSTATS = "/fitnessstats-service/activity"
    DELETE_ACTIVITY = "/activity-service/activity"

    # Downloads
    FIT_DOWNLOAD = "/download-service/files/activity"
    TCX_DOWNLOAD = "/download-service/export/tcx/activity"
    GPX_DOWNLOAD = "/download-service/export/gpx/activity"
    KML_DOWNLOAD = "/download-service/export/kml/activity"
    CSV_DOWNLOAD = "/download-service/export/csv/activity"

    # Upload
    UPLOAD = "/upload-service/upload"

    # Gear
    GEAR = "/gear-service/gear/filterGear"
    GEAR_BASEURL = "/gear-service/gear"

    # Badges & Challenges
    EARNED_BADGES = "/badge-service/badge/earned"
    AVAILABLE_BADGES = "/badge-service/badge/available"
    ADHOC_CHALLENGES = "/adhocchallenge-service/adHocChallenge/historical"
    BADGE_CHALLENGES = "/badgechallenge-service/badgeChallenge/completed"
    AVAILABLE_BADGE_CHALLENGES = "/badgechallenge-service/badgeChallenge/available"
    NON_COMPLETED_BADGE_CHALLENGES = "/badgechallenge-service/badgeChallenge/non-completed"
    INPROGRESS_VIRTUAL_CHALLENGES = "/badgechallenge-service/virtualChallenge/inProgress"

    # Personal Records & Goals
    PERSONAL_RECORD = "/personalrecord-service/personalrecord/prs"
    GOALS = "/goal-service/goal/goals"

    # Workouts & Training
    WORKOUTS = "/workout-service"
    WORKOUTS_SCHEDULE = "/workout-service/schedule"
    CALENDAR = "/calendar-service"
    SCHEDULED_WORKOUTS = "/calendar-service"
    TRAINING_PLAN = "/trainingplan-service/trainingplan"

    # Nutrition
    NUTRITION = "/nutrition-service"
    NUTRITION_DAILY_FOOD_LOGS = "/nutrition-service/food/logs"
    NUTRITION_DAILY_MEALS = "/nutrition-service/meals"
    NUTRITION_DAILY_SETTINGS = "/nutrition-service/settings"

    # Golf
    GOLF = "/gcs-golfcommunity/api/v2"
    GOLF_SCORECARD_SUMMARY = "/gcs-golfcommunity/api/v2/scorecard/summary"
    GOLF_SCORECARD_DETAIL = "/gcs-golfcommunity/api/v2/scorecard/detail"
    GOLF_SHOT = "/gcs-golfcommunity/api/v2/shot/scorecard"

    # System
    REQUEST_RELOAD = "/wellness-service/wellness/epoch/request"
    SOLAR = "/web-gateway/solar"
    GRAPHQL_ENDPOINT = "graphql-gateway/graphql"
    DAILY_LIFESTYLE_LOGGING = "/lifestylelogging-service/dailyLog"
