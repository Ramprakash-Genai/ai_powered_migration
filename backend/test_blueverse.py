from services.blueverse_client import call_blueverse_agent


test_input = {
    "execution_mode": "INITIAL_MIGRATION",
    "source_language": "java",
    "target_language": "java",
    "source_bdd": "cucumber",
    "target_bdd": "playwright",
    "original_source_code": "driver.findElement(By.id(\"login\")).click();",
    "user_feedback": None
}

response = call_blueverse_agent(test_input)
print(response)