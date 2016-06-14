from optparse import OptionParser
from random import randint
import random
import os, sys, json
import math
import StringIO
'''
TODO:
- big problem with non-unique solutions, current code tries to
  remove some edges in order to make the queries unique, in particular   
  when we detect the duplicate paths we find the first event no already used
  and remove it. The problem is that we do not know "if the event is used" in 
  possible resulting path.
'''

class EventData:
    _max_int = sys.maxint-1
    def __init__(self):
        self.status = 0 
        self.connections = []
        self.n_use=0;
        self.reset()
    def add(self, event):
        self.connections.append(event)
    def visited(self):
        return self.status >0
    def expanded(self):
        return self.status >1
    def visit(self):
        self.status = 1
    def expand(self):
        self.status = 2
    def reset(self):
        self.previous_all = []
        self.n_transits = EventData._max_int
    def update(self,  previous_event, transits):
        self.previous_all = [ previous_event ]
        self.n_transits = transits
    def append_previous(self,  previous_event):
        self.previous_all.append(previous_event)


class Idos :
    def __init__(self):
        self.events = {}
        
    def read_graph(self, in_stream):
        '''
        Graph verticis are pairs (station, time) for
        every leave or arrive time in the same station.
        Edges are either connections between stations
        or edges connecting subsequent times of the single stations.
        
        We first read connection edges and create vertices per 
        '''

        row=in_stream.next()
        (n_stations, n_connections) = [int(item) for item in row.split()]

        # for every event list of edges in form (target_event, travel_time)    
        # events per station in order to create waiting connections.
        station_times = d = [[] for i in xrange(n_stations)]
        for i_conn in range(n_connections) :
            row = in_stream.next()
            #print "row: ", row
            (u,v,t_leave, t_travel) = [int(item) for item in row.split()]

            u_vtx = (u, t_leave)
            v_vtx = (v, t_leave + t_travel)
            #print "add: " , u_vtx, v_vtx
            station_times[u].append(t_leave)
            station_times[v].append(t_leave + t_travel)                        
            if (not u_vtx in self.events) :
                self.events[u_vtx]=EventData()              
            self.events[u_vtx].add( v_vtx )
            if (not v_vtx in self.events) :
                self.events[v_vtx]=EventData()              
        
        
        for (i_station, station_schedule) in enumerate(station_times):
            station_schedule.sort()
            #print station_schedule
            for first, second in zip(station_schedule, station_schedule[1:]) :
                if ( not first == second ):
                    target_event = (i_station, second)                    
                    self.events[(i_station, first)].add(target_event)
                
        self.topological_sort()
        #print self.topological
        #for key,e in self.events.iteritems():
        #    print >>sys.stderr, key, e.__dict__
        
    def topological_sort(self):
        '''
        Make topological sort using DFS, order reverse of postvisit times
        So we push back the events at postivisit into toplogical list.
        Node states:
        0 - no visit 
        1 - visited, pushed on stack
        2 - childs generated
        
        Alternative, just sort by event times.
        '''
        
        self.topological=[]
        stack=[]
        for (event, event_data) in self.events.iteritems():
            if (not event_data.visited()) :
                stack.append(event)
                event_data.visit()
                while (stack) :
                    top_event = stack[-1]
                    top_event_data = self.events[top_event]
                    if (not top_event_data.expanded()):
                        # just added to stack
                        top_event_data.expand()
                        for edge in top_event_data.connections:
                            ngh_event = edge
                            ngh_event_data = self.events[ngh_event]
                            if (not ngh_event_data.visited()) :
                                stack.append(ngh_event)
                    else:
                        # close the event node
                        stack.pop()
                        self.topological.append(top_event)    
                        
    def reset(self):
        for event in self.events:
            self.events[event].reset()


    def get_path(self, event):
        '''
        Return the path to given event in the reversed order.
        Path is represented by the list of transit events including start and target event.
        If the path is not unique return None.
        If the path does not exist return empty list.        
        '''
        path = []
        while (True):
            event_data = self.events[event]
            # check for the start event
            if (event_data.previous_all[0] == event):
                break
            if (not path or path[-1][0] != event[0]):
                path.append(event)            
            if len(event_data.previous_all) != 1:
                return [ event ] 
            event = event_data.previous_all[0]
        path.append(event) # append start event
        return path
        
    def simplify_previous(self, event):
        '''
        Try to remove some events to force unique path.
        
        - Find any path, prefering already used events. (possible improvement searching path through used events.)
        - Mark events as used.
        - Remove all unused events.
        - Fail if any used events out of the path.
        
        '''
        # Find any path, mark used events.
        #print >>sys.stderr, "simplify: ", event
        
        path = []
        while (True):
            event_data = self.events[event]
            # check for the start event
            #print >>sys.stderr, "check : ", event
            if (event_data.previous_all[0] == event):
                break
            if (not path or path[-1][0] != event[0]):
                path.append(event)            
            event_data.n_use +=1
            new_event = event_data.previous_all[0]    
            for previous in event_data.previous_all:
                if self.events[previous].n_use > 0:
                    new_event = previous
            #print >>sys.stderr, "delete : ", event
            event=new_event
            event_data.previous_all=[]        
        path.append(event) # append start event
        self.events[event].n_use +=1
        
        # Remove unused events.
        for event, data in self.events.iteritems():
            if data.previous_all:
                if data.n_use == 0:
                    # keep only waiting edge
                    nghs = data.connections                    
                    data.connections = [ngh for ngh in nghs if ngh[0]==event[0]]
                else:
                    return None
        return path 
    
    
    def graph_output(self, stream):
        string_stream = StringIO.StringIO()
        n_edges=0
        stations=[]
        for event,data in self.events.iteritems():
            stations.append(event[0])
            #print >>sys.stderr, data.connections
            for ngh in data.connections:                
                string_stream.write("{0} {1} {2} {3}\n".format(event[0], ngh[0], event[1], ngh[1]-event[1]) )
                n_edges +=1
        n_stations = len(set(stations))
        stream.write( "{0} {1}\n".format(n_stations, n_edges))
        stream.write(string_stream.getvalue())

        
    def print_path(self, out_stream, path):
        if (not path):
            out_stream.write("()\n")
            return
        
        for e in reversed(path):
            #out_stream.write("({0} {1} {2}) ".format(e[0], e[1], self.events[e].n_transits))
            out_stream.write("({0} {1}) ".format(e[0], e[1]))
        out_stream.write("\n")    
        
        
        
 



    def use_events_on_path(self, path):
        '''
        Increase usage counter for get in events on the path.
        Do  not apply to the target event (the first in the path).
        '''
        for event in path[1:]:
            self.events[event].n_use += 1
            
            
    def solve_case(self, in_stream, check_unique = False):        
        '''
        Read setting from the input stream, returns the path or dag of the solution. Or empty list if no path
        exists.
        '''
        row = in_stream.next()
        #print "case: ", row 
        (start_station, target_station, start_time) = [int(item) for item in row.split()]
        # skip all up to the start event
        for event in reversed(self.topological):
            if (event[1] >= start_time):
                #print event    
                event_data = self.events[event]
                # check for start station
                if (event[0] == start_station):                    
                    event_data.update(event, 0) # set previous to itself
                
                # skip events that are not descendants of the start event
                if (not event_data.previous_all):
                    continue
                
                # check that we get to target
                
                if (event[0] == target_station):                    
                    return self.get_path(event)
                
                #print >>sys.stderr, event    
                #print event_data.connections
                for edge in event_data.connections:
                    ngh_event = edge
                    ngh_event_data = self.events[ngh_event]
                    alt_transits = event_data.n_transits
                    if event[0] != ngh_event[0]:
                        alt_transits += 1
                    #print >>sys.stderr, "  ngh:", event, ngh_event
                    if (ngh_event_data.n_transits > alt_transits):
                        #print "update"
                        ngh_event_data.update(event, alt_transits)
                        #print "  NG:",ngh_event, self.events[ngh_event].__dict__
                    else:
                        if (check_unique):                            
                            ngh_event_data.append_previous(event)
        else:            
            # no way to target station
            return []
            

def make_data(in_stream, problem_size):
    '''
    For every station, get random number of outgoing connections,
    random outcome times, random target stations, random travel time.
    '''
    graph_stream = StringIO.StringIO()
    
    graph = []
    for i_station in range(problem_size):
        n_connections = random.randrange(10, 12*24)
        times = []
        for i_conn in range(n_connections):
            times.append( random.randrange(0, 60*24-10) )
        times=sorted(set(times))
        last_connection = None
        for time in times:
            target_station = random.randrange(0, problem_size -1)
            if target_station >= i_station:
                target_station+=1                
            assert i_station != target_station    
            max_travel_time = min( 60*24 - time-1, 15)                
            travel_t = random.randrange(1, max_travel_time)    
            connection = (i_station, target_station, time, travel_t)
            if ( last_connection and connection[0:2] == last_connection[0:2]):
                continue
            graph.append(connection)
            last_connection = connection
    
    graph_stream.write( "{0} {1}\n".format(problem_size, len(graph)))
    for edge in graph:
        graph_stream.write( "{0} {1} {2} {3}\n".format(edge[0], edge[1], edge[2], edge[3]) )
        
    graph_stream.seek(0)
    graph = Idos()
    graph.read_graph(graph_stream)
    
    query_stream = StringIO.StringIO()
    # queries
    n_queries = int(1 + math.sqrt(problem_size))
    query_stream.write("{0}\n".format(n_queries))
    i_duplicates=0
    i_case=0
    while i_case < n_queries:
        start = random.randrange(0, problem_size -1)
        target = random.randrange(0, problem_size -1)
        time =  random.randrange(0, 60*24/2)        
        case = "{0} {1} {2}\n".format(start, target, time)
        graph.reset()
        path = graph.solve_case(StringIO.StringIO(case), check_unique=True)        
        if len(path) != 1:           
            graph.use_events_on_path(path)
            query_stream.write(case)
            i_case+=1
        else:
            if graph.simplify_previous(path[0]) != None:
                query_stream.write(case)
                i_case+=1
            else:    
                i_duplicates+=1
            #print >> sys.stderr, "duplicate case: ", start, target, time                   
    #print >> sys.stderr, "duplicates: ", i_duplicates, " from: ", n_queries
    
    # output reduced graph
    graph.graph_output(in_stream)
    in_stream.write(query_stream.getvalue())
    


def solve(in_stream, out_stream) :
    idos = Idos()
    idos.read_graph(in_stream)
    n_cases = int(in_stream.next())
    for i_case in range(0,n_cases) :        
        path = idos.solve_case(in_stream)
        assert path != None, "Non-unique solution."
        idos.print_path(out_stream, path)
        idos.reset()



'''
Main script body.
'''

parser = OptionParser()
parser.add_option("-p", "--problem-size", dest="size", help="Problem size.", default=None)
parser.add_option("-v", "--validate", action="store_true", dest="validate", help="program size", default=None)
parser.add_option("-r", dest="rand", default=False, help="Use non-deterministic algo")

options, args = parser.parse_args()

random.seed(1234)

if options.rand:
    random.seed(options.rand)

if options.size is not None:
    make_data(sys.stdout, int(options.size))
else :
    solve(sys.stdin, sys.stdout)
