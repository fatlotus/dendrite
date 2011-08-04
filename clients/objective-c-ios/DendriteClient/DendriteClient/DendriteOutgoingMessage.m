//
//  DendriteOutgoingMessage.m
//  DendriteClient
//
//  Created by Jeremy Archer on 7/29/11.
//  Copyright 2011 University of Chicago CI. All rights reserved.
//

#import "DendriteClient.h"

@interface DendriteOutgoingMessage (hidden)

- (id)initWithDendriteClient:(DendriteClient *)client;
- (NSInvocation*)invocationForTypeID:(NSUInteger)typeID;

@end

@implementation DendriteOutgoingMessage

@synthesize respondingToMessage, userInfo;

- (id)initWithDendriteClient:(DendriteClient *)client
{
    self = [super init];
    
    if (self != nil) {
        parentClient = client;
        
        respondingToMessage = nil;
        userInfo = nil;
    }
    
    return self;
}

- (NSInvocation*)invocationForTypeID:(NSUInteger)typeID
{
    return responseTable[typeID];
}

- (void)respondToReply:(DendriteMessageType)type withSelector:(SEL)selector
{
    NSInvocation * invocation = [NSInvocation invocationWithMethodSignature:[parentClient.delegate methodSignatureForSelector:selector]];
    
    [invocation setSelector:selector];
    [invocation retain];
    
    responseTable[[DendriteClient typeIDFromType:type]] = invocation;
}

@end
