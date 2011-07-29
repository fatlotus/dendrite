//
//  DendriteIncomingMessage.h
//  DendriteClient
//
//  Created by Jeremy Archer on 7/29/11.
//  Copyright 2011 University of Chicago CI. All rights reserved.
//

#import <Foundation/Foundation.h>
#import "DendriteClient.h"

@interface DendriteIncomingMessage : NSObject {
    NSUInteger messageID;
    DendriteClient * parentClient;
}

- (DendriteOutgoingMessage *)replyWithType:(DendriteMessageType)type andArguments:(id)argument, ...;

@end
