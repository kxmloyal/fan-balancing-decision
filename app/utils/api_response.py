from flask import jsonify


class ApiResponse:
    @staticmethod
    def success(data=None, message="操作成功", status_code=200):
        body = {"success": True, "message": message}
        if data is not None:
            body["data"] = data
        return jsonify(body), status_code

    @staticmethod
    def error(message="操作失败", status_code=400, data=None):
        body = {"success": False, "message": message}
        if data is not None:
            body["data"] = data
        return jsonify(body), status_code

    @staticmethod
    def ok():
        return jsonify({"success": True, "message": "OK"}), 200
