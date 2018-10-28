#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: wuyue
# Email: wuyue@mofanghr.com

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Table, Text
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Database(object):
    def __init__(self, db_url, **kwargs):
        self.engine = create_engine(db_url, **kwargs)
        DBSession = sessionmaker(bind=self.engine)
        self.session = DBSession()

    def init_table(self):
        return Base.metadata.create_all(self.engine)

    def delete_table(self):
        return Base.metadata.drop_all(self.engine)


class ResumeRaw(Base):
    __tablename__ = 'resume_raw'

    id = Column(Integer, primary_key=True, nullable=False)
    source = Column(String(50), index=True)
    email = Column(String(50))
    subject = Column(String(255))
    content = Column(String)
    processStatus = Column(String(50))
    parsedTime = Column(DateTime)
    reason = Column(String)
    emailJobType = Column(String(50))
    emailCity = Column(String(50))
    createTime = Column(DateTime, primary_key=True, nullable=False)
    createBy = Column(String(50))
    updateTime = Column(DateTime)
    updateBy = Column(String(50))
    trackId = Column(String(255))
    resumeUpdateTime = Column(String(30))
    resumeSubmitTime = Column(String(30))
    avatarUrl = Column(String(255))
    ip = Column(String(100))

