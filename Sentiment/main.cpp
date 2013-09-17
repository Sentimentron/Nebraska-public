//
//  main.cpp
//  Sentiment
//
//  Created by Richard Townsend on 17/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#include <iostream>
#include "PLSentenceSource.h"

int main(int argc, const char * argv[])
{

    // insert code here...
    std::cout << "Hello, World!\n";
    PLSentenceSource *p;
    p = new PLSentenceSource();
    std::vector<Sentence *> sv = p->GetSentences();
    
    for(std::vector<Sentence *>::iterator it = sv.begin(); it != sv.end(); ++it) {
        Sentence *s = *it; 
        std::cout << s->GetClassificationStr() << " " << s->GetText() << "\n";
    }
    
    delete p;
    return 0;
}

