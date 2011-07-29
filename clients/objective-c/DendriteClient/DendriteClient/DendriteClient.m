//
//  DendriteClient.m
//  DendriteClient
//
//  Created by Jeremy Archer on 7/29/11.
//  Copyright 2011 University of Chicago CI. All rights reserved.
//

#import "DendriteClient.h"
#import "DendriteOutgoingMessage.h"
#import "DendriteIncomingMessage.h"

@implementation DendriteClient

#pragma mark Table conversion methods

- (DendriteMessageType)typeFromTypeID:(NSUInteger)typeID
{
    return dendriteMessageTypeTable[typeID];
}

- (NSUInteger)typeIDFromType:(DendriteMessageType)type
{
    for (NSUInteger i = 0; i < kDendriteHighestTypeIDPlusOne; i++) {
        if (dendriteMessageTypeTable[i] == type) {
            return i;
        }
    }
    
    [NSException raise:@"UndefinedType" format:@"Unknown message type."];
    return 0;
}

#pragma mark - Constructors

- (id)initWithAddress:(NSString*)string port:(NSUInteger)port andDelegate:(id)defaultDelegate
{
    self = [super init];
    
    if (self != nil) {
        for (NSUInteger i = 0; i < kDendriteHighestTypeIDPlusOne; i++) {
            invocation[i] = nil;
        }
        
        delegate = defaultDelegate;
    }
    
    return self;
}

#pragma mark - Public Interface


- (DendriteOutgoingMessage *)sendMessage:(DendriteMessageType)type
                           withArguments:(id)argument, ...
{
    DendriteOutgoingMessage * msg = [[DendriteOutgoingMessage alloc] initWithClient:self andMessageID:sendingMessageID];
    
    /* send message over socket */
    
    return msg;
}

- (void)handleMessages:(DendriteMessageType)type
          withSelector:(SEL)selector
{
    NSUInteger typeID = [self typeIDFromType:type];
    
    if (defaultResponses[typeID] != nil) {
        [NSException raise:@"InvalidInvocation" format:@""];
    }
    
    NSInvocation * invocation = [NSInvocation invocationWithMethodSignature:[delegate methodSignatureForSelector:selector]];
    [invocation setTarget:delegate];
    [invocation setSelector:selector];
    [invocation retain];
    
    defaultResponses[typeID] = invocation;
}

@end
