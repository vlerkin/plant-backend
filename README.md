## Project Description
-- non-tech part --
PlantieCare project was created as my graduation project at Mind Mingle Bootcamp. It solves several problems my friends and I have as plants owners.

Helps to track care of your plants (watering, fertilisers and diseases);
Gives you opportunity to share your plants with a friend/family member who is planning to take care after them while you are travelling or absent, a caretaker does not need to register, they can simply scan a QR code or use a provided link to gain restricted access to your plants and log watering.
-- tech part --
The app has a responsive design with "mobile first" approach at it's core.  
Although during the bootcamp we mostly focused on JS technologies in all our projects, for this particular one, I decided to challenge myself by incorporating new technologies I had never used before: FastAPI, SQLAlchemy, Pydantic, AWS S3, and Tailwind. It was a great challenge, to build an entire app from sctratch using several unfamiliar technologies within 2.5 weeks and now I am happy to present the result. For code delivery I used docker containers (also for development), the project is deployed on AWS EC2.

To access the app, please, navigate here: https://plantie-care.klestova.nl/  
To access API documentation, please, check out this link: https://plantie-care-api.klestova.nl/docs#/  

## What functionality the app has
In PlantieCare you can:  

1. Create a user and log into the app (register and login), you can add your photo and edit personal info in your account;  
2. Add plant cards with instructions about plant care, add a photo, edit plant info or delete a plant;  
3. Add watering, fertilisers and diseases with treatment or without;  
4. You can see all plants on my-plants page or navigate to a page of a specific plant to read/add more info;  
5. In your profile, you can add permissions to access your plants for caretakers and manage them;  
6. You can share access via QR code or link, the caretaker will be authorized with the given credentials, caretaker does not need to register. If a caretaker is already a user of the app, they will be logged out and authorised with the new credentials, granting them limited access to your plants. Limited access means they can only log watering activities, and nothing else.  

## Backend technologies
The backend for this project was developed using Python 3, with FastAPI serving as the framework for the REST API. Pydantic was employed for data validation, while SQLAlchemy acted as the ORM for database queries. PostgreSQL was chosen as the database system. Passwords are stored in the database utilising hashing.   
To handle authentication, an auth middleware was created following the guidelines in the FastAPI documentation. This middleware is based on JSON Web Tokens (JWTs), specifically utilising the Jose package. To grant limited access to guest users (caretakers) 'aud' parameter was used, it specifies validity of the token for resource servers. Access to different pages, including ones that use dynamic routing, for guest tokens was specified using regular expressions.  
The code for file uploading was mainly inspired by the FastAPI documentation, as well as related articles and solutions found on platforms like Stack Overflow. Further storing of photos performed with AWS S3.  
All dependencies necessary for the backend components of the project were documented in the requirements.txt file.  
