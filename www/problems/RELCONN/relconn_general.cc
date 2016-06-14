#include <sstream>

#include <iostream>
#include <fstream>
#include <cstdlib>
#include <algorithm>
#include <cmath>
#include <vector>
#include <utility>
#include <queue>
#include <unordered_set>

using namespace std;

typedef unsigned int uint;


class Exc : public std::exception {
  public:      
      Exc(string str)
      : str_(str)
      {}
      virtual ~Exc() noexcept {}
      
      const char*  what() const noexcept {
          return str_.c_str();
      }
      string str_;
  };


/**
 * Priority queue. It stores indexes with their values.
 * Value provides:
 * - Default constructor of Value sets value to the maximum value (using its comparison).
 * - Copy constructor, etc. what vector<Value> needs
 */
template <class Value>
class PriorityQueue {
public:
  
  
  struct HeapValue {      
      Value value;
      // back reference to the heap
      uint heap_idx;
  };
  
  PriorityQueue(uint n) {
    heap_items_.resize(n+1);
    heap.resize(n+1);
    for(uint idx=1; idx<n+1; idx++) {
        heap[idx]=idx;
        heap_items_[idx].heap_idx = idx;
    }        
  }

  uint size() {
      return heap.size()-1;
  }
  
  inline bool in_queue(uint idx) {
      //cerr << "idx: " << idx << " hidx: " << heap_items_[ idx ].heap_idx << endl;
      return heap_items_[ idx +1 ].heap_idx!=0;
  }
  
  inline Value operator[](uint idx) {
      return heap_items_[idx+1].value;
  }
   
  uint pop_front() {      
    // heap pop
    uint front_idx = heap[1];  
    Value &front_value = heap_items_[ heap[1] ].value;
    remove_heap_item(1);
    // update heap
    uint ii=1; uint min,l,r;
    while (1) {
      min=ii, l=2*ii, r=2*ii+1;
      if (l < heap.size() && heap_lt(l,min)) min=l;
      if (r < heap.size() && heap_lt(r,min)) min=r;
      if (min == ii) break;
      heap_swap(ii,min);
      ii=min;
    }      
    return front_idx-1;
  }  
  
  void update(uint index, Value value) {
   HeapValue &heap_value =  heap_items_[index+1];
   //cout << value << " < " << heap_value.value;
   if (value < heap_value.value) {
      //cout << " TRUE" << endl; 
      heap_value.value = value;
      uint ii=heap_value.heap_idx;
      while (ii >1 && heap_lt(ii, ii/2)) {
        heap_swap(ii,ii/2);
        ii=ii/2;
      }  
    } else {
        //cout << " FALSE" << endl;
    }
  }  

private:  
  inline void remove_heap_item(uint heap_idx) {
    //cerr << "hidx: " << heap_idx << " idx: " << heap[heap_idx] << endl; 
    heap_items_[ heap[heap_idx] ].heap_idx=0; // remove from heap
    heap[heap_idx]= heap.back();
    heap.pop_back();
    heap_items_[ heap[heap_idx] ].heap_idx=heap_idx;
  }  
  
  inline void heap_swap(uint i, uint j) {
    heap_items_[heap[i]].heap_idx=j;
    heap_items_[heap[j]].heap_idx=i;
    swap(heap[i],heap[j]);
  }  
  
  inline bool heap_eq(uint heap_i, uint heap_j) {
    if (heap_j >= heap.size()) return false;
    if (heap_i == heap_j) return false;
//    cerr << heap[heap_i] << "==" << heap[heap_j] << " "
//         << heap_items_[heap[heap_i]].value << " " << heap_items_[heap[heap_j]].value << endl;
    return heap_items_[heap[heap_i]].value == heap_items_[heap[heap_j]].value;
  }  

  inline bool heap_lt(uint heap_i, uint heap_j) {
    return heap_items_[heap[heap_i]].value < heap_items_[heap[heap_j]].value;
  }  

 

  Value zero;
  // For the position in the heap gives position in items_heap_
  // This provides also the index of particular value.
  vector<uint> heap;
  // Values in orginal position.
  vector<HeapValue> heap_items_;
};  



/**
 * Solve reads data from the input stream and output data to the output stream.
 * 
 * Errors should be reported to cerr and/or thow an exception.
 * 
 * Solve can return some characteristics of the result.
 * 
 * Here we return number of strongly connected components.
 */ 

struct Edge {
    uint target;
    double prob;
};

struct DijkstraVtx {
    uint previous;
    double prob;
    
    DijkstraVtx() {
        previous = (uint)(-1);
        prob = 0.0;
    }
    
    /**
     * Returns true if this is 'better' then other.
     */
    bool operator <(const DijkstraVtx &other) {        
        return this->prob > other.prob;
    }

    bool operator ==(const DijkstraVtx &other) {        
        return this->prob == other.prob;
    }

};

ostream &operator <<(ostream &os, const DijkstraVtx &vtx) {
    os << "( " << vtx.previous << ", " << vtx.prob << " )";
    return os;
}

struct Dijkstra {
    uint n_vtx, n_edg;
    vector< vector< Edge > > graph;  
    
    void read_graph(istream &in) {
        in >> n_vtx;
        in >> n_edg;
        graph.resize(n_vtx);  
        
        uint v_source, v_target;
        double e_prob;
        for(uint ie=0; ie<n_edg; ie++) {
            in >>v_source; in >> v_target; in >> e_prob;
            graph[v_source].push_back({v_target,e_prob});
            graph[v_target].push_back({v_source,e_prob});
        }       
    }

    void solve_case(istream &in, ostream &out) {
      uint connection_source, connection_target, min_idx;  
      in >> connection_source;
      in >> connection_target;
      
      //cerr << "case: " << connection_source << " " << connection_target << endl;
      PriorityQueue<DijkstraVtx> queue(n_vtx);      
      DijkstraVtx source_vtx;
      source_vtx.prob=1.0;
      queue.update(connection_source, source_vtx);
            
      while (queue.size() > 0) {
          min_idx = queue.pop_front();
          //cerr << "min_idx: " << min_idx << " size: " << queue.size() << endl;
          auto min_vtx = queue[min_idx];
          if (min_vtx.prob == 0) { // vertex not connected as well as remaining
              min_idx = connection_source;
              break;
          }
          if (min_idx == connection_target) {
              break;
          }          

          //cout << "src: " << connection_source << " trg: " << connection_target
          //     << " min: " << min_idx << " size: " << graph.size() << endl;
          for(auto &ngh : graph[min_idx]) {
              double alt_prob = ngh.prob * min_vtx.prob;
              //cerr << "    ngh: " << ngh.target << " closed: " << queue.in_queue(ngh.target)
              //<< " alt: " 
              //<< alt_prob << " prob: " << queue[ngh.target].prob <<endl;
              if (! queue.in_queue(ngh.target)) continue;
              if (alt_prob == queue[ngh.target].prob) {
                  /*
                   // print conflicting paths
                  cerr << "vtx: " << ngh.target << " min: " << min_idx <<  " p: " << alt_prob << endl;
                  uint idx = ngh.target;
                  while (idx != uint(-1)) {
                      cerr << queue[idx];
                      idx = queue[idx].previous;
                  }    
                  cerr << endl;
                  idx = min_idx;  
                  while (idx != uint(-1)) {
                      cerr << queue[idx];
                      idx = queue[idx].previous;
                  }    
                  cerr << endl;*/
                  throw(Exc("Nonunique solution."));
              }
              if (alt_prob > queue[ngh.target].prob) {
                  DijkstraVtx value;
                  value.previous = min_idx;
                  value.prob = alt_prob;
                  queue.update(ngh.target, value);                  
              }
                 
          }
      }

      vector<uint> path;
      if (min_idx == connection_target) {                    
          for(;min_idx != connection_source; ) {              
              path.push_back(min_idx);
              uint prev = queue[min_idx].previous;
              if (prev == uint(-1)) 
                  cerr << "wrong previous for: " << min_idx << endl;
              min_idx = prev;    
          }    
      }
      path.push_back(connection_source);
      for(uint i=path.size()-1; i!=uint(-1); i--) {          
          out << path[i] << " ";
      }    
      out << endl;        
    }
};


int solve( istream &in, ostream &out) {
  Dijkstra dijkstra;
  dijkstra.read_graph(in);
  
  uint n_query;
  in >> n_query;
  for(uint i_query=0; i_query < n_query; i_query++) {
      dijkstra.solve_case(in,out);
  }
}



/**
 * make random oriented multigraph with loops
 * it is guaranteed, that number of componends is at least n_comp which is randomly generated
 * up to max_n_comp constant.
 * 
 * size - number of vertices
 * min_ngh, max_ngh - range of number of outcomming edges from single vertex 
 * n_comp - number of components
 */ 

struct Coord {
    double x,y,power;
};

double runiform() {
    return rand()/double(RAND_MAX);
}

// symmetric hash
struct pair_uint_hash {
     inline std::size_t operator()(const std::pair<uint,uint> & v) const {
        return (v.first+1)*(v.second+1);
    }
};

void make_dataset(ostream &out_stream, uint n_vtx, uint n_edge_per_vtx, uint n_query) {
    
    unordered_set< pair<uint,uint>, pair_uint_hash > edge_flag;
    edge_flag.reserve(2*n_vtx*n_edge_per_vtx);
    
    // First make graph connections, random undirected graph.
    vector< vector<Edge> > edges(n_vtx);
    uint n_edge = 0;
    for(uint u=0; u<n_vtx; u++) {
        //cerr << "u: " << u << endl;
        for(uint i_ngh=0; i_ngh<n_edge_per_vtx; i_ngh++) {
            // random vtx different from u
            uint v = (u + rand()%(n_vtx-1)+1)%n_vtx;           
            if ( edge_flag.find({u,v}) == edge_flag.end() && 
                 edge_flag.find({v,u}) == edge_flag.end() ) {   
                // every edge is stored only once (at bigger vtx)
                //double prob = (1+erf(4*runiform()))/2;    
                double prob = 0.5+0.4999*runiform();    
                n_edge++;
                edges[u].push_back({v, prob});
                edge_flag.insert({u,v});
            } else {                
                i_ngh--; // try again
                //cerr << "   i_ngh: " << i_ngh << " v: " << v << endl;
            }    
        }           
    }
    
    
    // graph output
    stringstream graph_out;
    graph_out << n_vtx << " " << n_edge << endl;
    for(uint i_row=0; i_row<edges.size(); i_row++) {        
        for(auto &ngh : edges[i_row]) 
            graph_out << i_row << " " << ngh.target << " " << ngh.prob << endl;
    }    
    
    //cerr   << graph_out.str();
   
    
    out_stream << graph_out.str();
    out_stream << n_query << endl;
    
    
    Dijkstra dijkstra;
    dijkstra.read_graph(graph_out);
    
    // queries
    uint iq=0;
    uint n_cycle=0;
    //n_query=5;
    while(iq< n_query) {
        n_cycle++;
        uint u = uint(runiform() * n_vtx)%n_vtx;
        uint v = uint(runiform() * n_vtx)%n_vtx;
        
        stringstream case_in, case_out;
        case_in << u << " " << v <<endl;
        try {
            dijkstra.solve_case(case_in, case_out);
        } catch ( Exc e ) {
            cerr << "Nonunique solution: " << case_in.str();
            
            continue;
        }
        
        iq++;        
        out_stream <<  case_in.str();                
    }   
    //cerr << "ratio: " << n_query/double(n_cycle) <<  endl;
}  
  
  
/**
 * Creates the test input data for the problem.
 * The problem size is given. The result data are output to the stream 'out'.
 * No checking should be performed. It is done by separate solve step.
 */  
void make_data(ostream &out, unsigned int problem_size) {
  uint n_vtx = problem_size;  
  uint n_edge_per_vtx = min(uint(10), uint(problem_size/3) );
  uint n_query = min(uint(50), n_vtx);

  stringstream input_data;
  make_dataset(input_data, n_vtx, n_edge_per_vtx, n_query);  
 
  stringstream solve_output;
  solve(input_data, solve_output);  
 
  out << input_data.str();  
}

int main(int argc, char* argv[]) {
    unsigned int problem_size = 0;
    uint random_seed=problem_size;
    
    for(int i =1; i<argc;i++) {       
        if (argv[i] == string("-p") ) {
            i++;
            if (i < argc) 
                stringstream(argv[i]) >> problem_size;
        } else if (argv[i] == string("-r")) {
            i++;
            if (i < argc) {
                istringstream ss(argv[i]);                    
                ss >> random_seed;
                if (ss.fail()) {
                    random_seed=problem_size; i--;
                }   
            }                           
        }
    }
    srand (random_seed);

    if (problem_size == 0) {
      solve( cin, cout);
    } else { 
      stringstream input_data;  
      make_data(input_data, problem_size );
      
      /*
      try {
        stringstream output_data;  
        solve(input_data, output_data);    
      } catch (...) {
        cerr << "Solve fails for generated data." << endl;
        throw;
      } */ 
      
      cout << input_data.str();
    }
    
    //
    //make_dataset("webisl_1000",1002, 4, 100);
    //make_dataset("webisl_10000",10374, 5,10);
    //make_dataset("webisl_1000000",987032, 2 , 20);
}