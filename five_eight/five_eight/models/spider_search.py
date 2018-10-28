# coding: utf-8
from sqlalchemy import Column, DateTime, String, text
from sqlalchemy.dialects.mysql import INTEGER, MEDIUMTEXT
from crwy.utils.sql.sqlalchemy_m import Base


class ResumeRaw(Base):
    __tablename__ = 'resume_raw'

    id = Column(INTEGER(11), primary_key=True, nullable=False,
                autoincrement=True)
    source = Column(String(50))
    email = Column(String(50))
    subject = Column(String(255))
    content = Column(MEDIUMTEXT)
    processStatus = Column(String(50))
    parsedTime = Column(DateTime)
    reason = Column(MEDIUMTEXT)
    emailJobType = Column(String(50))
    emailCity = Column(String(50))
    deliverJobName = Column(String(50))
    deliverJobCity = Column(String(50))
    createTime = Column(DateTime, nullable=False)
    createBy = Column(String(50))
    updateTime = Column(DateTime)
    updateBy = Column(String(50))
    trackId = Column(String(255))
    resumeUpdateTime = Column(String(30))
    resumeSubmitTime = Column(String(30))
    rdCreateTime = Column(DateTime, primary_key=True, nullable=False,
                          server_default=text("CURRENT_TIMESTAMP"))
