# from flask_sqlalchemy import SQLAlchemy

# db = SQLAlchemy()

# class PhoneNumber(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     phone_number = db.Column(db.String(20), unique=True, nullable=False)
#     nickname = db.Column(db.String(50), nullable=False)

# class RandomNick(db.Model): #랜덤 닉네임(영문4)
#     id = db.Column(db.Integer, primary_key=True)
#     phone_number = db.Column(db.String(13), unique=True)
#     rand_nickname = db.Column(db.String(4))
#     def __repr__(self):
#         return f'<RandomNick {self.rand_nickname}>'