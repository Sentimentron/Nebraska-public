import csv
import sys

if __name__ == "__main__":

    with open(sys.argv[1], "r") as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=',')
        for row in csv_reader:
            for postfix in ["","second"]:
                if len(postfix) == 0:
                    tweet_postfix = ""
                else:
                    tweet_postfix = "2"
                tweet1 = row["Input.tweet%s" % (tweet_postfix,)]
                print "Tweet: %s" % (tweet1, )
                tweet1 = tweet1.split(" ")
                print [(i+1, word) for i, word in enumerate(tweet1)]
                phrase_counter = 1
                for i in [1,2]:
    # "HITId","HITTypeId","Title","Description","Keywords","Reward","CreationTime","MaxAssignments","RequesterAnnotation","AssignmentDurationInSeconds","AutoApprovalDelayInSeconds","Expiration","NumberOfSimilarHITs","LifetimeInSeconds","AssignmentId","WorkerId","AssignmentStatus","AcceptTime","SubmitTime","AutoApprovalTime","ApprovalTime","RejectionTime","RequesterFeedback","WorkTimeInSeconds","LifetimeApprovalRate","Last30DaysApprovalRate","Last7DaysApprovalRate","Input.id","Input.tweet","Input.id2","Input.tweet2","Answer.id","Answer.idsecond","Answer.phrase1begin","Answer.phrase1beginsecond","Answer.phrase1end","Answer.phrase1endsecond","Answer.phrase1words","Answer.phrase2begin","Answer.phrase2beginsecond","Answer.phrase2end","Answer.phrase2endsecond","Answer.phrase2words","Answer.phrase2wordssecond","Answer.phrase3end","Answer.phrase3endsecond","Answer.phrase3words","Answer.phrase3wordssecond","Answer.phrase4end","Answer.phrase4endsecond","Answer.phrase4words","Answer.phrase4wordssecond","Answer.sentiment","Answer.sentimentphrase1","Answer.sentimentphrase1second","Answer.sentimentphrase2","Answer.sentimentphrase2second","Answer.sentimentphrase3","Answer.sentimentphrase3second","Answer.sentimentphrase4","Answer.sentimentphrase4second","Approve","Reject"

                    phrase_start_key = "Answer.phrase%dbegin%s" % (i, postfix)
                    phrase_end_key   = "Answer.phrase%dend%s" % (i, postfix)
                    phrase_sent_key  = "Answer.sentimentphrase%d%s" % (i,postfix)

                    phrase_start = row[phrase_start_key]
                    phrase_end   = row[phrase_end_key]
                    phrase_sent = row[phrase_sent_key]
                
                    if len(phrase_start) == 0 or len(phrase_end) == 0:
                        break 

                    print phrase_start
                    
                    if i == 1:
                        phrase_start = [int(phrase_start)]
                        phrase_end   = [int(phrase_end)]
                        phrase_sent = [phrase_sent]
                    else:
                        phrase_start = [phrase for phrase in phrase_start.split("|") if len(phrase) > 0]
                        phrase_end = []
                        for j in [2,3,4]:
                            phrase_end_key   = "Answer.phrase%dend%s" % (j, postfix)
                            phrase_end_val   = row[phrase_end_key]
                            if len(phrase_end_val) == 0:
                                break
                            phrase_end_val   = int(phrase_end_val)
                            phrase_end.append(phrase_end_val)
                        
                        print phrase_start, phrase_end
                        phrase_start = [int(i) for i in phrase_start]
                        phrase_end   = [int(i) for i in phrase_end]
                        phrase_sent = []
                        for j in [2, 3, 4]:
                            phrase_sent_key  = "Answer.sentimentphrase%d%s" % (j, postfix) 
                            phrase_sent_val = row[phrase_sent_key]
                            phrase_sent.append(phrase_sent_val)
                            
                    for j, (pstart, pend, psent) in enumerate(zip(phrase_start, phrase_end, phrase_sent)):
                       print j, pstart, pend, psent
                       print "Phrase %d: %s (%s)" % (phrase_counter, ' '.join(tweet1[pstart-1:pend]), psent)
                       phrase_counter += 1
                raw_input("\nPress any key to continue")
                    
