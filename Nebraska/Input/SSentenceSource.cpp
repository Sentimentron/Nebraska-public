//
//  SanalyticsReader.cpp
//  Sentiment
//
//  Created by Richard Townsend on 01/10/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#include "SSentenceSource.h"
#include <fstream>
#include <sstream>
#include <algorithm>

void ReadCSV(std::ifstream &file, std::vector<std::vector<std::string>> &lines) {
    bool bufquote = false;
    bool bufline  = false;
    std::string buf;
    lines.clear();
    std::vector<std::string> line;
    char b;
    while ((b = file.get()) != EOF) {
        switch (b) {
            case '"':
                bufline = false;
                bufquote = !bufquote;
                break;
            case ',':
                bufline = false;
                if (bufquote) buf += b;
                else {
                    line.push_back(buf);
                    buf.clear();
                }
                break;
            case '\n':
            case '\r':
                if (bufquote) buf += b;
                else if (!bufline) {
                    line.push_back(buf);
                    lines.push_back(line);
                    buf.clear(); line.clear();
                    bufline = true;
                }
                break;
            default:
                bufline = false;
                buf.push_back(b);
                break;
        }
    }
    if (buf.size()) {
        line.push_back(buf);
    }
    if (line.size()) {
        lines.push_back(line);
    }
}

SSentenceSource::SSentenceSource(std::string path) {
    std::ifstream in(path, std::ios::in | std::ios::binary);
    std::vector<std::vector<std::string>> contents;
    std::vector<std::vector<std::string>>::iterator it;
    // Double-check the file opened
    if (!in) throw(errno);
    // Read the file
    ReadCSV(in, contents);
    // Iterate over the contents
    it = contents.begin();
    // "Topic","Sentiment","TweetId","TweetDate","TweetText"
    while (it != contents.end()) {
        it++; // Skip header row 
        if (it == contents.end()) break;
        Sentence            *s;
        ClassificationLabel label;
        auto fields = *it;
        if (fields.size() < 5) continue;
        // Recognize the label
        std::string slabel = fields[1];
        if (slabel == "irrelevant") continue;
        if (slabel == "positive") {
            label = PositiveSentenceLabel;
        }
        else if (slabel == "negative") {
            label = NegativeSentenceLabel;
        }
        else {
            continue;
        }
        // Create the sentence
        std::transform(fields[4].begin(), fields[4].end(), fields[4].begin(), ::tolower);
        s = new Sentence(label, fields[4].c_str());
        this->sentences.push_back(s);
    }
}