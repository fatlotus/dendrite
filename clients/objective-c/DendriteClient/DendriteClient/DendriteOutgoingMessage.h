//
//  DendriteOutgoingMessage.h
//  DendriteClient
//
//  Created by Jeremy Archer on 7/29/11.
//  Copyright 2011 __MyCompanyName__. All rights reserved.
//

#import <Foundation/Foundation.h>
#import "DendriteClient.h"

@interface DendriteOutgoingMessage : NSObject {
    NSInvocation * responseTable[kDendriteHighestTypeIDPlusOne];
    DendriteClient * parentClient;
}

- (void)respondToReply:(DendriteMessageType)type withSelector:(SEL)selector;

@end
