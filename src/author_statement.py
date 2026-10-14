"""Author notice shared by the application and documentation."""
from i18n import tr

CONTACT = 'peekaboocatx@gmail.com'
AUTHOR = 'XT (XuTao)'


def statement_html():
    return ('<h2>' + tr('作者声明') + '</h2><p>'
            + tr('本项目由 XT（XuTao）发起，并在大模型辅助下开发。') + '</p><p>'
            + tr('项目源码按 GNU AGPLv3 提供，第三方组件遵循各自许可。') + '</p><p>'
            + tr('未经作者授权，作者不提供商用部署、商业定制或相关支持。该支持政策不限制 GNU AGPLv3 赋予的权利。')
            + '</p><h2>' + tr('致谢') + '</h2><p>'
            + tr('感谢湖南科技大学、湖南科技大学计算机科学与工程学院以及服务计算与软件服务新技术湖南省重点实验室提供的学习与科研环境。')
            + '</p><p><a href="https://www.hnust.edu.cn/">' + tr('湖南科技大学')
            + '</a><br><a href="https://computer.hnust.edu.cn/">' + tr('湖南科技大学计算机科学与工程学院')
            + '</a></p><h2>' + tr('建议与联系') + '</h2><p><a href="mailto:' + CONTACT + '">' + CONTACT + '</a></p>')
