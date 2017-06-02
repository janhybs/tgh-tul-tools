#include <iostream>
#include <sstream>
#include <cmath>
#include <cstdlib>
#include <vector>
#include <exception>
using namespace std;


#undef DEBUG

#ifdef DEBUG
#define dout cout << "DBG: "
#else
#define dout ostream(0)
#endif


class NonUnique : public std::exception {
};

typedef unsigned int uint;


struct Vtx {
  uint idx;
  int heap_idx;
  uint ix,iy;
  int dist_rock; // actual cheapest edge to MST
  uint dist_entrance; //  actual distance from entrance
  uint mst_parent; // actual incomming edge
  
  // indexing of edges: east(1), west(2), south(4), north(8)
  uint rock[4]; // hardness of the rock, for closed vtx: -1 no edge , -2 edge in MST 
  int ngh[4]; // neighbour vtx 
  
  
  inline bool gt(uint rock, uint entrance) const {
    return (dist_rock > rock) ||
    (dist_rock == rock && dist_entrance > entrance);
  }
  
  
  inline bool operator <(const Vtx&other) {
    return other.gt(dist_rock, dist_entrance);
  }
  
  inline void neq(uint rock, uint entrance) const {
    if (dist_rock == rock && dist_entrance == entrance) {
            cerr 
            << dist_rock << ", "
            << rock << ", "
            << dist_entrance << ", "
            << entrance << endl;
            throw NonUnique();
    }
  }
};

// edge position in the ngh vtx array
const int back_idx[4]={1, 0, 3, 2};

class PQ {
public:
  int count;
  
  inline PQ(uint n, uint m, uint seed) {
    int x_dir[4]={1,-1,0,0};
    int y_dir[4]={0,0,-1,1};
    count=0;

    if (std::min(m,n) <= 100)
        modulo = 256;
    else 
        modulo = 256*256;
    r_num=seed;
    //cout << "s: " << seed << "mod: " << modulo << endl;
    
    // make graph
    graph.resize(n*m);
    for(uint iy=0; iy<n; iy++)
      for(uint ix=0; ix<m; ix++) {
        uint idx=iy*m+ix;
        Vtx &vtx=graph[idx];
        vtx.ix=ix;
        vtx.iy=iy;
        vtx.idx=idx;
        vtx.dist_entrance=2*n*m;
        vtx.dist_rock=modulo;
        vtx.heap_idx=-1;
        vtx.mst_parent=-1;
        for(uint idir=0;idir<4;idir++) {
          int jx=ix+x_dir[idir];
          int jy=iy+y_dir[idir];
          if (jx<0 || jx>=m || jy<0 || jy>=n) {
            vtx.ngh[idir]=-1;
            vtx.rock[idir]=-1;
          } else {  
            vtx.ngh[idir]=jx+m*jy;
            vtx.rock[idir]=modulo;
          }  
          //cout <<  iy << " " << ix<<" " << idir << ":" << vtx.ngh[idir] << endl; 
        }  
      }  
    // init heap  
    heap.resize(n*m+1);
    for(uint j=0;j<n*m;j++) heap[j+1]=j,graph[j].heap_idx=j+1;
    graph[0].dist_entrance=0;
    graph[0].dist_rock=0;
    graph[0].mst_parent=-1;
  }  
  
  
  inline uint random() {
        
    r_num=((r_num * 1664525) + 1013904223)%modulo;
    return r_num;
  }  
  
  
  inline void heap_remove(uint idx) {
    graph[ heap[idx] ].heap_idx=-1;
    heap[idx]= heap.back();
    heap.pop_back();
    graph[ heap[idx] ].heap_idx=idx;
  }  
  
  
  inline void heap_swap(uint i, uint j) {
    graph[heap[i]].heap_idx=j;
    graph[heap[j]].heap_idx=i;
    swap(heap[i],heap[j]);
  }  
  
  
  inline bool heap_lt(uint i, uint j) {
      return graph[heap[i]] < graph[heap[j]];
  }  
  
  inline Vtx & pop_head() {
    // heap pop
    Vtx &vtx=graph[ heap[1] ];
    heap_remove(1);
    uint ii=1; uint min,l,r;
    while (1) {
      min=ii, l=2*ii, r=2*ii+1;
      if (l < heap.size() && heap_lt(l,min)) min=l;
      if (r < heap.size() && heap_lt(r,min)) min=r;
      if (min == ii) break;
      heap_swap(ii,min);
      ii=min;
    }  
    
    /*
    try {
      if (heap.size() > 1)  
        graph[ heap[1] ].neq(vtx.dist_rock, vtx.dist_entrance);
    } catch (NonUnique &e) {
        cerr << "vtx: " << vtx.idx << " , top: " << heap[1] << endl;
    }
    */
    
    // set rock
    //cout << vtx.idx<< "pop:" << vtx.mst_parent<< endl;
    for(uint j=0; j<4; j++) {  
      if ( vtx.ngh[j]>0 && vtx.rock[j] == modulo) {
        // set rock hardness to the neighbour vtx, 
        // need not to set for vtx since it is closed
        
        graph[ vtx.ngh[j] ].rock[ back_idx[j] ] = r_num;
        random();    
        
        //cout<< graph[ vtx.ngh[j] ].idx << " nh:" << back_idx[j] << " " 
        //   << graph[ vtx.ngh[j] ].rock[ back_idx[j] ] <<  endl;
      } else {
        //cout << vtx.rock[j] << ",";
      }  
      vtx.rock[j]=-1; // no MST edge
    }
    //cout << endl;
    
    // set edge codes for output
    if (vtx.mst_parent!=-1) {
      uint parent_idx=vtx.ngh[ vtx.mst_parent ];
      //cout << "set: " << vtx.idx << " " << vtx.mst_parent << endl;
      //cout << "set: " << parent_idx << " " << back_idx[ vtx.mst_parent ] << endl;
      graph[parent_idx].rock[ back_idx[ vtx.mst_parent ] ]=-2; // set MST edge
      vtx.rock[ vtx.mst_parent ] = -2;
    } else if (vtx.idx != 0) cerr << "no parent: " << vtx.idx << endl; 
    
    // close vtx
    vtx.dist_rock=-1;
    
    return vtx;
  }  
  
  inline void update(Vtx &vtx, int dist_rock, int dist_entrance) {
      vtx.neq(dist_rock, dist_entrance);
      vtx.dist_rock=dist_rock;
      vtx.dist_entrance = dist_entrance;
      uint ii=vtx.heap_idx;
      while (ii >1 && heap_lt(ii, ii/2)) {
        heap_swap(ii,ii/2);
        ii=ii/2;
      }    
  }  

  uint r_num, modulo; // seed, modulo of LCG
  uint size;    // heap size
  vector<uint> heap;
  vector<struct Vtx> graph;
};  


void solve( istream &in, ostream &out) {
  uint n, m, seed;
  in >> n;
  in >> m;
  in >> seed;
  
  
  PQ p_queue(n,m,seed);
  
  while (p_queue.heap.size() > 1) {
    // add next vtx to MST, generate new weights
    Vtx &next_vtx = p_queue.pop_head();  
    //cerr << "vtx: " << next_vtx.idx << endl;
    
    // update neighbours
    for(uint idir=0; idir<4; idir++) 
      if (next_vtx.ngh[idir] >0) { // neighbour exists, deals with borders
        // neighbour vtx
        Vtx &ngh=p_queue.graph[ next_vtx.ngh[idir] ];
        //cout<< ngh.idx << " ngh:" << back_idx[idir] << " " 
        //    << ngh.rock[ back_idx[idir] ] <<  endl;
        if (ngh.dist_rock==-1) continue; // skip closed vtx
        // update ngh
        uint alt_dist = next_vtx.dist_entrance + 1;         
        // complex access to the rock hardness due to already closed next_vtx
        uint alt_rock =ngh.rock[ back_idx[idir] ];

        if (ngh.gt(alt_rock, alt_dist)) {
          ngh.mst_parent=back_idx[idir];
          p_queue.update(ngh, alt_rock, alt_dist);
        }  
      }  
  }
  
  char digits[16]={'0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F'};
  //char digits[16]={' ',250,250,196,250,192,217,193,250,
  //                 218,191,194,179,195,180,197};
  // print result
  for(uint i=0; i<n; i++) {
    for(uint j=0; j<m; j++) {
      uint ii=i*m+j;
      uint code=0;
      uint power=1;
      for(uint k=0;k<4;k++, power*=2) {
        if (p_queue.graph[ii].rock[k] == -2) {
          code+=power;
          //cout <<","<< k << " ";
        }  
      }  
      out << digits[code]; 
    }
    out << endl;
  }
  //cout << "multi: " << p_queue.multi_mst << endl;
}




/**
 * Creates the test input data for the problem.
 * The problem size is given. The result data are output to the stream 'out'.
 * No checking should be performed. It is done by separate solve step.
 */  
void make_data(ostream &out, unsigned int problem_size) {
  while (1) {
    stringstream input, output;  
    uint sq = sqrt(problem_size);  
    uint n = sq/2 + rand()%sq;
    uint m =problem_size / n;
    input << n << " " << m << " " << rand()%256;
    
    // end when solution is unique
    try {
        cerr << "Try: " << input.str() << endl;
        solve(input, output);
    } catch (const NonUnique &e)  {
        continue;
    }
    out << input.str();
    break;
  }  
}



int main(int argc, char* argv[]) {
    unsigned int problem_size = 0;
    uint random_seed=problem_size;
    
    for(int i =1; i<argc;i++) {       
        if (argv[i] == string("-p") ) {
            i++;
            if (i < argc) 
                stringstream(argv[i]) >> problem_size;
                random_seed = problem_size;
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