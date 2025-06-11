pkill -f org.apache.flume.node.Application # 别的全杀了

flume-ng agent \
  --conf ./flume \
  --conf-file ./flume/flume-conf.properties \
  --name agent \
  -Dflume.root.logger=INFO,console