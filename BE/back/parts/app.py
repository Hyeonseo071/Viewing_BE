# # app.py
# from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
# from flask_cors import CORS

# db = SQLAlchemy()

# def create_app():
#     app = Flask(__name__)
#     app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost/viewinging'
#     app.config['SECRET_KEY'] = 'your_secret_key'
#     CORS(app)

#     db.init_app(app)

#     # Blueprint import는 app 생성 후에 수행하여 순환 참조 방지
#     from phone import phone_bp
#     app.register_blueprint(phone_bp, url_prefix='/api')

#     with app.app_context():
#         db.create_all()  # 필요한 경우 데이터베이스 테이블을 생성

#     return app

# if __name__ == "__main__":
#     app = create_app()
#     app.run(debug=True)
