from flask import render_template, redirect, url_for, request, g
from manager import admin

@admin.route('/main',methods=['GET'])
# Display an HTML page with links
def main():
    return redirect(url_for('main'))