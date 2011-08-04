//
//  DendriteIncomingMessage.m
//  DendriteClient
//
//  Created by Jeremy Archer on 7/29/11.
//  Copyright 2011 University of Chicago CI. All rights reserved.
//

#import "DendriteClient.h"

#pragma mark Private accessors
@interface DendriteIncomingMessage (hidden)

- (id)initWithClient:(DendriteClient *)client andMessageID:(NSUInteger)messageID;

@end

@interface DendriteClient (hidden)

- (DendriteOutgoingMessage *)sendMessage:(DendriteMessageType)type
                             withReplyTo:(NSUInteger)replyTo
                            andArguments:(NSArray*)arguments;

@end

#pragma mark Implementation

@implementation DendriteIncomingMessage

@synthesize respondingToMessage, userInfo;

- (id)initWithClient:(DendriteClient *)client
        andMessageID:(NSUInteger)theMessageID
{
    self = [super init];
    
    if (self != nil) {
        parentClient = client;
        messageID = theMessageID;
        
        respondingToMessage = nil;
        userInfo = nil;
    }
    
    return self;
}

- (DendriteOutgoingMessage *)replyWithType:(DendriteMessageType)type
                              andArguments:(id)argument, ...
{
    va_list args;
    va_start(args, argument);
    
    NSMutableArray * argumentsAsArray = [NSMutableArray arrayWithCapacity:10]; 
    
    NSUInteger numberOfArguments = strlen(dendriteMessageArgumentTypesTable[[DendriteClient typeIDFromType:type]]);
    
    if (numberOfArguments >= 1)
        [argumentsAsArray addObject:argument];
    
    for (NSUInteger i = 1, l = numberOfArguments; i < l; i++) {
        [argumentsAsArray addObject: va_arg(args, id)];
    }
    
    va_end(args);
    
    DendriteOutgoingMessage * message = [parentClient sendMessage:type withReplyTo:messageID andArguments:argumentsAsArray];
    
    message.respondingToMessage = self;
    
    return message;
}

@end
