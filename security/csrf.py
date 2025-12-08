from flask_wtf.csrf import CSRFProtect
from flask import Flask

class CSRFProtection:
    def __init__(self, app=None):
        self.csrf = CSRFProtect()
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """
        初始化CSRF保护
        
        Args:
            app (Flask): Flask应用实例
        """
        # 设置CSRF保护
        app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # CSRF令牌有效期1小时
        app.config['WTF_CSRF_SSL_STRICT'] = False  # 在HTTPS环境下宽松处理
        
        # 初始化CSRF保护
        self.csrf.init_app(app)
        
    def exempt(self, view):
        """
        为特定视图免除CSRF保护
        
        Args:
            view: 视图函数
            
        Returns:
            装饰器函数
        """
        return self.csrf.exempt(view)