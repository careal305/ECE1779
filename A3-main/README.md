# A3

ece1779 a3 restaurant review app : https://03rs8d4pzk.execute-api.us-east-1.amazonaws.com/production
email sender: ece1779a3@hotmail.com password: Ece1779pass

Settings
1. one user can only submit one comment for each restaurtant
2. one owner can only have one restaurant

Finished requirements
1. login panel(connect to DynamoDB) Completed
2. user/owner register route Completed
3. restaurant list
4. admin page (read all restaurants&reviews, delete all users/restaurants, create user)
5. review page(user-write a review, owner-reply to the comment)
6. write rewiew
7. owner reply page
8. compute average rating&update in restaurant table
9. forgot password(copy from a1) - gmail will block insecure login, we can try that later
10. change password(following forgot password, user should change to their own password after they received the temporary one)(not tested)

TO DO LIST:
Backend

Important information :
1. gmail: display unlock captcha(https://accounts.google.com/b/0/DisplayUnlockCaptcha) only remains for like 25 mins.
2. zappa tutorial:
   1) Go into the project directory
   2) Create a new python virtual environment as follows:
      $ python -m venv venv
   3) Activate the virtual environment:
      $ source venv/bin/activate
   4) Install any libraries/packages that you need to deploy your app:
      $ pip install flask
      $ pip install zappa
      $ pip install boto3
        ...
   5) Install AWS Command Line Interface (CLI)

   Follow instruction in https://aws.amazon.com/cli/
   6) Configure your credentials
   7) zappa command: (see https://github.com/Miserlou/Zappa for more details)
      $ zappa init
      $ zappa deploy production  # deploy your application, just follow the questions in the command lines
      
      $ zappa update production  # to update your production/code
      $ zappa undeploy production # to remove the API Gateway and Lambda function that you have previously published deactivate
      $ zappa tail production # check log of the deployments
        ...
      

!!Please DO NOT DELETE the first row(owner0, user0, admin) in the three tables(dynamodb), the reason is that if we delete all the items in a table, only the keys exist, the other items will disappear. So I create 3 default rows to keep all the items in case we click the delete users/restaurants in admin page.

