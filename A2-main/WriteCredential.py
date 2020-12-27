file = '/Users/chloez/.aws/credentials'
with open(file, 'w') as filetowrite:
    myCredential = """ [default]
aws_access_key_id=ASIAUYLVHMLRDK7JKJWH
aws_secret_access_key=IkdljoZu6CJNMzJ0TffWhW8SQKXW+AqleMxgNDJv
aws_session_token=FwoGZXIvYXdzEAQaDGLTWilES5K131eaeCLGATreFxMYX1UzxvETf0uy7JIH5IG4Ds+PVe47GgQswpQsCn7u+xWVYcpsQCaSpKH5KbxQHBLwUheMBbFhFqGxL5q8/mU/HOTaVOuVkGUzxD9P4SWGLeVZrTyrGS/dLARI27W5UjklMqpefusLiqbF3Lf0/cP651btg5Bp8PZ08Xy5ru1grDnDE1evOTKBRafdVaALWF/DYGYe650MLS9KBrrfN5mpa8DYr03ziDoQwudedjcaR0J+E2QMCVHjjLBnPCdFgZ0JoyiEwKT9BTItcJvXHBlQALdES1egwkahEZai2iLVlg5A5GX1rs/yinqxuUoUYeHu4E5TZrex"""
    filetowrite.write(myCredential)

file='/Users/chloez/.aws/config'
with open(file, 'w') as filetowrite:
    myCredential = """[default] 
                       region = us-east-1
                       output = json
                       [profile prod]
                       region = us-east-1
                       output = json"""
    filetowrite.write(myCredential)