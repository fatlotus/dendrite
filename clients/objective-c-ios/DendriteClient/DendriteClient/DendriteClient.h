//
//  DendriteClient.h
//  DendriteClient
//
//  Created by Jeremy Archer on 7/29/11.
//  Copyright 2011 University of Chicago CI. All rights reserved.
//

#import <Foundation/Foundation.h>

@class DendriteOutgoingMessage;
@class DendriteIncomingMessage;
@class AsyncSocket;


#pragma mark Generic Dendrite Client Configuration

#define kDendriteClientDefaultTimeout ((NSTimeInterval)30.0)

#pragma mark - Message Type Declarations (not shown)

typedef enum {
    _none,
    _endoflist,
    TypeEcho,
    TypeFetch,
    TypeListen,
    TypeNotify,
    TypeCancel,
    TypeData,
    TypeLogin,
    TypeSuccess,
    TypeFailure,
    TypeIdentity,
    TypeIdentify,
} DendriteMessageType;

#define kDendriteHighestTypeIDPlusOne 0x0E

extern DendriteMessageType dendriteMessageTypeTable[];
extern char * dendriteMessageArgumentTypesTable[];

#pragma mark - DendriteClientDelegate methods
@class DendriteClient;

@protocol DendriteClientDelegate
- (void)connectedWithClient:(DendriteClient *)client;
@end

@interface DendriteIncomingMessage : NSObject {
    NSUInteger messageID;
    DendriteClient * parentClient;
}

@end

@interface DendriteOutgoingMessage : NSObject {
    NSInvocation * responseTable[kDendriteHighestTypeIDPlusOne];
    DendriteClient * parentClient;
}

- (void)respondToReply:(DendriteMessageType)type withSelector:(SEL)selector;

@end

#pragma mark - Public Interface

@interface DendriteClient : NSObject {
    NSUInteger sendingMessageID, receivingMessageID;
    NSInvocation * defaultResponses[kDendriteHighestTypeIDPlusOne];
    NSMutableDictionary * messageResponseHandlers;
    AsyncSocket * socket;
    NSUInteger incomingMessageNonce, outgoingMessageNonce;
    id<DendriteClientDelegate> delegate;
    NSUInteger incomingMessageTypeID, incomingMessageReplyTo;
}

#pragma mark Constructors

- (id)initWithAddress:(NSString*)string port:(NSUInteger)port andDelegate:(id<DendriteClientDelegate>)delegate;

#pragma mark - Static Helpers

+ (DendriteMessageType)typeFromTypeID:(NSUInteger)typeID;
+ (NSUInteger)typeIDFromType:(DendriteMessageType)type;

#pragma mark - Public Methods

- (DendriteOutgoingMessage *)sendMessage:(DendriteMessageType)type
                           withArguments:(id)argument, ...;

- (void)handleMessages:(DendriteMessageType)type
          withSelector:(SEL)selector;

@property (nonatomic, readonly, assign) id<DendriteClientDelegate> delegate;

@end
