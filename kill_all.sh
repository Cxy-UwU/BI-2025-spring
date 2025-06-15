#!/bin/zsh
# kill_all.sh
# 杀掉所有占用9092端口的进程

PIDS=$(lsof -ti :9092)
if [ -z "$PIDS" ]; then
  echo "没有进程占用9092端口。"
else
  echo "杀掉以下进程: $PIDS"
  kill -9 $PIDS
  echo "已杀掉所有占用9092端口的进程。"
fi
