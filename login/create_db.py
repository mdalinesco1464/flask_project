from app import app, db

# Create the application context
with app.app_context():
    # Now you can access the application and perform operations within the context
    db.create_all()
