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

#pragma mark Message Type Declarations (not shown)

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

#define kDendriteHighestTypeIDPlusOne 0x0D

DendriteMessageType dendriteMessageTypeTable[] = {
    /*0x00*/ _none,
    /*0x01*/ TypeEcho,
    /*0x02*/ TypeFetch,
    /*0x03*/ TypeListen,
    /*0x04*/ TypeNotify,
    /*0x05*/ TypeCancel,
    /*0x06*/ _none,
    /*0x07*/ _none,
    /*0x08*/ TypeData,
    /*0x09*/ TypeLogin,
    /*0x0A*/ TypeSuccess,
    /*0x0B*/ TypeFailure,
    /*0x0C*/ TypeIdentity,
    /*0x0D*/ TypeIdentify
};

#pragma mark - Public Interface

@interface DendriteClient : NSObject {
    NSUInteger sendingMessageID, receivingMessageID;
    NSInvocation * defaultResponses[kDendriteHighestTypeIDPlusOne];
    id delegate;
}

#pragma mark Constructors

- (id)initWithAddress:(NSString*)string port:(NSUInteger)port andDelegate:(id)delegate;

#pragma mark - Public Methods

- (DendriteOutgoingMessage *)sendMessage:(DendriteMessageType)type
                           withArguments:(id)argument, ...;

- (void)handleMessages:(DendriteMessageType)type
          withSelector:(SEL)selector;

@end
