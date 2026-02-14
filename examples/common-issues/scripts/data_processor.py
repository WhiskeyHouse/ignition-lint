import system.tag

def read_count(line):
    tag = "[default]Line" + str(line) + "/ProductionCount"
    result = system.tag.readBlocking([tag])
    print result[0].value
    return result[0].value

def calc_eff(actual, target):
    return (actual / target) * 100

url = "http://192.168.1.100:8088/gateway"

def process():
    for i in xrange(1, 6):
        count = read_count(i)
        print "Line %d: %d" % (i, count)
