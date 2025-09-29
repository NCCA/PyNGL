from ncca.ngl import logger

# You can also log directly from your application code
# note we can get the logger from the ngl module as we created it there
logger.info("This is an info message from the application")
logger.warning("This is a warning message")
logger.error("This is an error message")

print("Logging test finished. Check the console and NGLDebug.log for output.")
